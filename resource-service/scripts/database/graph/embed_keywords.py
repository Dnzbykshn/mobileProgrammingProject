"""
`keyword_taxonomy_map` tablosundaki canonical keyword'leri embed eder
ve sonucu aynı tabloya geri yazar.

Kullanım:
    python scripts/database/graph/embed_keywords.py
"""

import os
import sys
import time
import logging
import psycopg2
from psycopg2.extras import execute_values
from google import genai
from dotenv import load_dotenv
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.database.common.embedding_cache import load_json_cache, save_json_cache

load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("❌  GEMINI_API_KEY tanımlı değil. .env dosyanızı kontrol edin.")

DB_PARAMS = {
    "host":     os.getenv("DB_HOST",     "localhost"),
    "database": os.getenv("DB_NAME",     "quranapp_resources_clean"),
    "user":     os.getenv("DB_USER",     "admin"),
    "password": os.getenv("DB_PASSWORD", ""),
    "port":     os.getenv("DB_PORT",     "5432"),
}

EMBEDDING_MODEL  = "models/gemini-embedding-001"
VECTOR_DIM       = 768
BATCH_SIZE       = 100   # Gemini embed_content tek çağrıda max ~100 metin destekler
RETRY_LIMIT      = 5
RETRY_BASE_DELAY = 10    # saniye (exponential backoff için baz)
GRAPH_CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "graph_keyword_embeddings.json"

client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------------------------------------------------------------------
# Step 1 – 'embedding' sütununu ekle (yoksa)
# ---------------------------------------------------------------------------

def ensure_embedding_column(conn: psycopg2.extensions.connection) -> None:
    """
    keyword_taxonomy_map tablosuna VECTOR(768) tipinde 'embedding' sütunu ekler.
    pgvector eklentisi zaten kuruluysa işlem anlık tamamlanır.
    """
    with conn.cursor() as cur:
        # pgvector eklentisini etkinleştir (zaten varsa idempotent)
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'keyword_taxonomy_map'
              AND column_name = 'embedding';
        """)
        if cur.fetchone() is None:
            cur.execute(f"""
                ALTER TABLE keyword_taxonomy_map
                ADD COLUMN embedding vector({VECTOR_DIM});
            """)
            log.info("✅  'embedding' sütunu oluşturuldu (VECTOR(%d)).", VECTOR_DIM)
        else:
            log.info("ℹ️   'embedding' sütunu zaten mevcut, atlandı.")
    conn.commit()

# ---------------------------------------------------------------------------
# Step 2 – Henüz vektörü olmayan keyword'leri çek
# ---------------------------------------------------------------------------

def fetch_pending_keywords(conn: psycopg2.extensions.connection) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT canonical_keyword
            FROM keyword_taxonomy_map
            WHERE embedding IS NULL
            ORDER BY canonical_keyword;
        """)
        rows = cur.fetchall()
    keywords = [r[0] for r in rows]
    log.info("📋  embedding IS NULL olan %d adet keyword bulundu.", len(keywords))
    return keywords


def load_db_embeddings(conn: psycopg2.extensions.connection) -> dict[str, list[float]]:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT canonical_keyword, embedding::text
            FROM keyword_taxonomy_map
            WHERE embedding IS NOT NULL
            ORDER BY canonical_keyword;
        """)
        rows = cur.fetchall()
    return {
        keyword: [float(value) for value in embedding.strip("[]").split(",")]
        for keyword, embedding in rows
        if embedding is not None
    }


def load_file_cache() -> dict[str, list[float]]:
    payload = load_json_cache(GRAPH_CACHE_FILE, default={"version": 1, "items": {}})
    return payload.get("items", {})


def save_file_cache(cache: dict[str, list[float]]) -> None:
    save_json_cache(GRAPH_CACHE_FILE, {"version": 1, "items": cache})


def restore_from_file_cache(
    conn: psycopg2.extensions.connection,
    pending_keywords: list[str],
    cache: dict[str, list[float]],
) -> list[str]:
    reusable = [(keyword, cache[keyword]) for keyword in pending_keywords if keyword in cache]
    if reusable:
        write_embeddings(conn, reusable)
        log.info("💾  Dosya cache'ten %d keyword geri yüklendi.", len(reusable))
    reusable_keys = {keyword for keyword, _ in reusable}
    return [keyword for keyword in pending_keywords if keyword not in reusable_keys]

# ---------------------------------------------------------------------------
# Step 3 – Gemini Embedding API (batch, retry + exponential backoff)
# ---------------------------------------------------------------------------

def embed_batch(texts: list[str], attempt: int = 0) -> list[list[float]]:
    """
    Verilen metin listesini Gemini ile vektörize eder.
    Hata durumunda exponential backoff ile RETRY_LIMIT kadar yeniden dener.
    """
    try:
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=texts,
            config={"output_dimensionality": VECTOR_DIM},
        )
        return [emb.values for emb in result.embeddings]
    except Exception as exc:
        if attempt < RETRY_LIMIT:
            delay = RETRY_BASE_DELAY * (2 ** attempt)
            log.warning(
                "⚠️   API hatası (deneme %d/%d): %s — %ds sonra yeniden denenecek.",
                attempt + 1, RETRY_LIMIT, exc, delay,
            )
            time.sleep(delay)
            return embed_batch(texts, attempt + 1)
        else:
            log.error("❌  %d denemeden sonra batch başarısız oldu: %s", RETRY_LIMIT, exc)
            raise

# ---------------------------------------------------------------------------
# Step 4 – Vektörleri veritabanına geri yaz
# ---------------------------------------------------------------------------

def write_embeddings(
    conn: psycopg2.extensions.connection,
    pairs: list[tuple[str, list[float]]],
) -> None:
    """
    [(canonical_keyword, embedding_vector), ...] listesini
    keyword_taxonomy_map tablosuna toplu UPDATE eder.
    """
    with conn.cursor() as cur:
        # pgvector, Python list'i doğrudan [x,y,...] formatında kabul eder.
        execute_values(
            cur,
            """
            UPDATE keyword_taxonomy_map AS t
            SET    embedding = data.embedding::vector
            FROM   (VALUES %s) AS data(kw, embedding)
            WHERE  t.canonical_keyword = data.kw;
            """,
            [(kw, str(vec)) for kw, vec in pairs],
            template="(%s, %s)",
        )
    conn.commit()

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    log.info("🚀  Graph RAG Keyword Embedding (v5) başlatılıyor...")
    log.info("    Model   : %s", EMBEDDING_MODEL)
    log.info("    Boyut   : %d", VECTOR_DIM)
    log.info("    Batch   : %d", BATCH_SIZE)

    conn = psycopg2.connect(**DB_PARAMS)

    try:
        # 1. Sütun kontrolü / oluşturma
        ensure_embedding_column(conn)

        file_cache = load_file_cache()
        db_embeddings = load_db_embeddings(conn)
        merged_cache = dict(file_cache)
        merged_cache.update(db_embeddings)
        if merged_cache != file_cache:
            save_file_cache(merged_cache)

        # 2. Bekleyen keyword'leri çek
        keywords = fetch_pending_keywords(conn)
        keywords = restore_from_file_cache(conn, keywords, merged_cache)
        if not keywords:
            log.info("💾  Dosya cache hazır: %d keyword", len(merged_cache))
            log.info("✅  Tüm keyword'ler zaten vektörize edilmiş. İşlem yok.")
            return

        total        = len(keywords)
        batches      = [keywords[i : i + BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
        total_batches = len(batches)
        start_time   = time.time()

        log.info("🔄  Toplam %d batch işlenecek.", total_batches)

        for batch_idx, batch in enumerate(batches, start=1):
            batch_start = time.time()

            # 3. Vektörize et
            vectors = embed_batch(batch)

            # 4. DB'ye yaz
            pairs = list(zip(batch, vectors))
            write_embeddings(conn, pairs)
            for keyword, vector in pairs:
                merged_cache[keyword] = vector
            save_file_cache(merged_cache)

            # ---- İlerleme & tahmini kalan süre ----
            elapsed      = time.time() - start_time
            done_kw      = batch_idx * BATCH_SIZE
            done_kw      = min(done_kw, total)
            pct          = done_kw / total * 100
            avg_per_kw   = elapsed / done_kw
            remaining_kw = total - done_kw
            eta_sec      = avg_per_kw * remaining_kw
            batch_ms     = (time.time() - batch_start) * 1000

            log.info(
                "   [%d/%d]  ✔ %d kw tamamlandı  |  %.1f%%  |  "
                "Batch: %.0fms  |  Tahmini kalan: %s",
                batch_idx,
                total_batches,
                done_kw,
                pct,
                batch_ms,
                _fmt_seconds(eta_sec),
            )

            # Rate-limit koruması: son batch değilse 1 saniye bekle
            if batch_idx < total_batches:
                time.sleep(1)

        total_time = time.time() - start_time
        log.info(
            "🎉  Tamamlandı! %d keyword vektörize edildi. Toplam süre: %s",
            total,
            _fmt_seconds(total_time),
        )
        log.info("💾  Dosya cache güncellendi: %d keyword", len(merged_cache))

    finally:
        conn.close()


def _fmt_seconds(seconds: float) -> str:
    """Saniyeyi okunabilir 'Xd Xh Xm Xs' formatına çevirir."""
    seconds = max(0, int(seconds))
    m, s    = divmod(seconds, 60)
    h, m    = divmod(m, 60)
    d, h    = divmod(h, 24)
    parts   = []
    if d: parts.append(f"{d}g")
    if h: parts.append(f"{h}s")
    if m: parts.append(f"{m}d")
    parts.append(f"{s}sn")
    return " ".join(parts)


if __name__ == "__main__":
    main()
