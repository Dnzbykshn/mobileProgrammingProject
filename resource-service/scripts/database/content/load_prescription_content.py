import argparse
import json
import os
import sys
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from scripts.database.common.embedding_cache import load_json_cache, save_json_cache

load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("❌ GEMINI_API_KEY tanımlı değil. .env dosyanızı kontrol edin.")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "quranapp_resources_clean"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}

ESMA_FILE = PROJECT_ROOT / "data" / "esma_enriched.json"
DUA_FILE = PROJECT_ROOT / "data" / "duas_enriched.json"
PRESCRIPTION_CACHE_FILE = PROJECT_ROOT / "data" / "cache" / "prescription_embeddings.json"

client = genai.Client(api_key=GEMINI_API_KEY)


def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    vectors: list[list[float]] = []
    for index in range(0, len(texts), batch_size):
        batch = texts[index:index + batch_size]
        time.sleep(1)
        result = client.models.embed_content(
            model="models/gemini-embedding-001",
            contents=batch,
            config={"output_dimensionality": 768},
        )
        vectors.extend(embedding.values for embedding in result.embeddings)
    return vectors


def parse_vector_text(value: str | None) -> list[float] | None:
    if value is None:
        return None
    return [float(item) for item in value.strip("[]").split(",")]


def build_esma_embed_text(item: dict) -> str:
    return " ".join(item["psychological_benefits"]) + " " + item["meaning"]


def build_dua_embed_text(item: dict) -> str:
    return item["context"] + " " + " ".join(item["emotional_tags"])


def load_prescription_file_cache() -> dict:
    return load_json_cache(PRESCRIPTION_CACHE_FILE, default={"version": 1, "esma": {}, "duas": {}})


def save_prescription_file_cache(cache: dict) -> None:
    save_json_cache(PRESCRIPTION_CACHE_FILE, cache)


def load_esma_cache(cur: psycopg2.extensions.cursor) -> dict[str, tuple[str, list[float]]]:
    cur.execute("SELECT to_regclass('public.esma_ul_husna');")
    if cur.fetchone()[0] is None:
        return {}

    cur.execute("""
        SELECT appellation, meaning, psychological_benefits, embedding::text
        FROM esma_ul_husna
        WHERE embedding IS NOT NULL;
    """)
    cache = {}
    for appellation, meaning, benefits, embedding in cur.fetchall():
        text = " ".join(benefits or []) + " " + (meaning or "")
        cache[appellation] = (text, parse_vector_text(embedding))
    return cache


def load_dua_cache(cur: psycopg2.extensions.cursor) -> dict[tuple[str, str], tuple[str, list[float]]]:
    cur.execute("SELECT to_regclass('public.prophet_duas');")
    if cur.fetchone()[0] is None:
        return {}

    cur.execute("""
        SELECT source, turkish_text, context, emotional_tags, embedding::text
        FROM prophet_duas
        WHERE embedding IS NOT NULL;
    """)
    cache = {}
    for source, turkish_text, context, emotional_tags, embedding in cur.fetchall():
        text = (context or "") + " " + " ".join(emotional_tags or [])
        cache[(source, turkish_text)] = (text, parse_vector_text(embedding))
    return cache


def reset_table(cur: psycopg2.extensions.cursor, table_name: str) -> None:
    cur.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")


def insert_esma(cur: psycopg2.extensions.cursor) -> int:
    print(f"📂 {ESMA_FILE} okunuyor...")
    with open(ESMA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    file_cache = load_prescription_file_cache()
    db_cache = load_esma_cache(cur)
    reset_table(cur, "esma_ul_husna")

    items = data.get("items", [])
    prepared: list[tuple[dict, list[float] | None]] = []
    missing_texts: list[str] = []
    missing_indexes: list[int] = []
    reused = 0

    for item in items:
        embed_text = build_esma_embed_text(item)
        file_cached = file_cache.get("esma", {}).get(item["appellation"])
        db_cached = db_cache.get(item["appellation"])
        if file_cached and file_cached["text"] == embed_text and file_cached["embedding"] is not None:
            prepared.append((item, file_cached["embedding"]))
            reused += 1
        elif db_cached and db_cached[0] == embed_text and db_cached[1] is not None:
            prepared.append((item, db_cached[1]))
            reused += 1
        else:
            prepared.append((item, None))
            missing_texts.append(embed_text)
            missing_indexes.append(len(prepared) - 1)

    if missing_texts:
        new_embeddings = embed_texts(missing_texts)
        for index, vector in zip(missing_indexes, new_embeddings):
            prepared[index] = (prepared[index][0], vector)

    updated_cache = file_cache
    for item, vector in prepared:
        updated_cache["esma"][item["appellation"]] = {
            "text": build_esma_embed_text(item),
            "embedding": vector,
        }
    save_prescription_file_cache(updated_cache)

    count = 0
    for item, vector in prepared:
        cur.execute(
            """
            INSERT INTO esma_ul_husna
            (name, appellation, meaning, psychological_benefits, referral_note, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                item["name"],
                item["appellation"],
                item["meaning"],
                item["psychological_benefits"],
                item["zmir_recommendation"],
                vector,
            ),
        )
        count += 1

    print(f"ℹ️ Esma embedding reuse: {reused}, yeni: {len(missing_texts)}")
    return count


def insert_duas(cur: psycopg2.extensions.cursor) -> int:
    print(f"📂 {DUA_FILE} okunuyor...")
    with open(DUA_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    file_cache = load_prescription_file_cache()
    db_cache = load_dua_cache(cur)
    reset_table(cur, "prophet_duas")

    items = data.get("items", [])
    prepared: list[tuple[dict, list[float] | None]] = []
    missing_texts: list[str] = []
    missing_indexes: list[int] = []
    reused = 0

    for item in items:
        embed_text = build_dua_embed_text(item)
        cache_key = (item["source"], item["turkish_text"])
        file_cached = file_cache.get("duas", {}).get(f"{item['source']}||{item['turkish_text']}")
        db_cached = db_cache.get(cache_key)
        if file_cached and file_cached["text"] == embed_text and file_cached["embedding"] is not None:
            prepared.append((item, file_cached["embedding"]))
            reused += 1
        elif db_cached and db_cached[0] == embed_text and db_cached[1] is not None:
            prepared.append((item, db_cached[1]))
            reused += 1
        else:
            prepared.append((item, None))
            missing_texts.append(embed_text)
            missing_indexes.append(len(prepared) - 1)

    if missing_texts:
        new_embeddings = embed_texts(missing_texts)
        for index, vector in zip(missing_indexes, new_embeddings):
            prepared[index] = (prepared[index][0], vector)

    updated_cache = file_cache
    for item, vector in prepared:
        updated_cache["duas"][f"{item['source']}||{item['turkish_text']}"] = {
            "text": build_dua_embed_text(item),
            "embedding": vector,
        }
    save_prescription_file_cache(updated_cache)

    count = 0
    for item, vector in prepared:
        cur.execute(
            """
            INSERT INTO prophet_duas
            (source, arabic_text, turkish_text, context, emotional_tags, embedding)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                item["source"],
                item["arabic_text"],
                item["turkish_text"],
                item["context"],
                item["emotional_tags"],
                vector,
            ),
        )
        count += 1

    print(f"ℹ️ Dua embedding reuse: {reused}, yeni: {len(missing_texts)}")
    return count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prescription içeriklerini PostgreSQL'e yükler.")
    parser.add_argument(
        "--only",
        choices=("all", "esma", "duas"),
        default="all",
        help="Sadece seçilen veri grubunu yükle.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    try:
        if args.only in {"all", "esma"}:
            count = insert_esma(cur)
            print(f"✅ {count} Esma kaydı yazıldı.")

        if args.only in {"all", "duas"}:
            count = insert_duas(cur)
            print(f"✅ {count} dua kaydı yazıldı.")

        conn.commit()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
