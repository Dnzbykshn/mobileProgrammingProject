import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    sys.exit("❌ GEMINI_API_KEY tanımlı değil.")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "quranapp_resources_clean"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}

MODEL = "models/gemini-3-flash-preview"
RETRY_LIMIT = 5
RETRY_DELAY = 10
BATCH_SIZE = 100

client = genai.Client(api_key=GEMINI_API_KEY)
TAXONOMY_FILE = PROJECT_ROOT / "data" / "graph_rag" / "taxonomy.json"
PROGRESS_FILE = PROJECT_ROOT / "data" / "graph_rag" / "categorization_progress.json"


def parse_vector_text(value: str | None) -> list[float] | None:
    if value is None:
        return None
    return [float(item) for item in value.strip("[]").split(",")]


def load_taxonomy() -> dict[str, list[str]]:
    with open(TAXONOMY_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def get_canonical_keywords() -> list[str]:
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT canonical_keyword FROM knowledge_units_graph_keywords ORDER BY 1;")
    keywords = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return keywords


def load_progress() -> dict[str, dict[str, str]]:
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"mapped": {}}


def save_progress(progress: dict[str, dict[str, str]]) -> None:
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as file:
        json.dump(progress, file, ensure_ascii=False, indent=2)


def prune_progress(
    progress: dict[str, dict[str, str]],
    valid_keywords: set[str],
    valid_subcategories: set[str],
) -> dict[str, str]:
    mapped = progress.get("mapped", {})
    filtered = {
        keyword: subcategory
        for keyword, subcategory in mapped.items()
        if keyword in valid_keywords and subcategory in valid_subcategories
    }
    if filtered != mapped:
        progress["mapped"] = filtered
        save_progress(progress)
    return filtered


def build_prompt(batch_keywords: list[str], subcategories: list[str]) -> str:
    valid_categories_str = "\n".join(f"- {subcategory}" for subcategory in subcategories)
    target_keywords_str = "\n".join(f"- {keyword}" for keyword in batch_keywords)
    return f"""Sen bir Türkçe klinik psikoloji ve Graph RAG ontoloji uzmanısın.
Aşağıda sabit alt kategori listesi var.

GÖREV:
Her hedef kelimeyi tek bir alt kategori ile eşleştir.

KURALLAR:
1. Yeni kategori uydurma.
2. Sadece geçerli JSON dön.
3. Her hedef kelime cevapta yer alsın.

GEÇERLİ ALT KATEGORİLER:
{valid_categories_str}

HEDEF KELİMELER:
{target_keywords_str}
"""


def call_gemini(prompt: str, valid_subcategories: list[str], retry: int = 0) -> dict[str, str] | None:
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config={
                "temperature": 0.0,
                "response_mime_type": "application/json",
            },
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        result = json.loads(text.strip())
        if isinstance(result, list):
            if result and isinstance(result[0], dict):
                result = result[0]
            else:
                raise ValueError("JSON çıktı sözlük değil.")
        if not isinstance(result, dict):
            raise ValueError("JSON çıktı sözlük değil.")

        validated: dict[str, str] = {}
        for keyword, category in result.items():
            if category in valid_subcategories:
                validated[keyword] = category
                continue
            fallback = next(
                (
                    valid
                    for valid in valid_subcategories
                    if category.lower() in valid.lower() or valid.lower() in category.lower()
                ),
                valid_subcategories[0],
            )
            validated[keyword] = fallback

        return validated
    except Exception as exc:
        if retry < RETRY_LIMIT:
            print(f"   ⚠️ Hata (retry {retry + 1}/{RETRY_LIMIT}): {exc}")
            time.sleep(RETRY_DELAY)
            return call_gemini(prompt, valid_subcategories, retry + 1)
        print(f"   ❌ {RETRY_LIMIT} denemeden sonra başarısız: {exc}")
        return None


def load_existing_embeddings(cur: psycopg2.extensions.cursor) -> dict[str, list[float]]:
    cur.execute("SELECT to_regclass('public.keyword_taxonomy_map');")
    if cur.fetchone()[0] is None:
        return {}

    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'keyword_taxonomy_map' AND column_name = 'embedding';
    """)
    if cur.fetchone() is None:
        return {}

    cur.execute("""
        SELECT canonical_keyword, embedding::text
        FROM keyword_taxonomy_map
        WHERE embedding IS NOT NULL;
    """)
    return {
        canonical_keyword: parse_vector_text(embedding)
        for canonical_keyword, embedding in cur.fetchall()
        if embedding is not None
    }


def main() -> None:
    print("🚀 Keyword kategorizasyonu başlıyor...")

    taxonomy = load_taxonomy()
    subcategory_to_root: dict[str, str] = {}
    valid_subcategories: list[str] = []
    for root, subcategories in taxonomy.items():
        for subcategory in subcategories:
            subcategory_to_root[subcategory] = root
            valid_subcategories.append(subcategory)

    all_keywords = get_canonical_keywords()
    valid_keyword_set = set(all_keywords)
    progress = load_progress()
    mapped = prune_progress(progress, valid_keyword_set, set(valid_subcategories))

    unmapped_keywords = [keyword for keyword in all_keywords if keyword not in mapped]

    print(f"📂 alt kategori: {len(valid_subcategories)}")
    print(f"📂 canonical keyword: {len(all_keywords)}")
    print(f"🎯 tamamlanan: {len(mapped)}")
    print(f"🎯 kalan: {len(unmapped_keywords)}")

    if unmapped_keywords:
        batches = [
            unmapped_keywords[index:index + BATCH_SIZE]
            for index in range(0, len(unmapped_keywords), BATCH_SIZE)
        ]
        for batch_index, batch in enumerate(batches, start=1):
            print(f"   [{batch_index}/{len(batches)}] {len(batch)} kelime işleniyor...")
            result = call_gemini(build_prompt(batch, valid_subcategories), valid_subcategories)
            if result is None:
                sys.exit("❌ Kategorizasyon tamamlanamadı.")
            for keyword in batch:
                mapped[keyword] = result.get(keyword, valid_subcategories[0])
            progress["mapped"] = mapped
            save_progress(progress)
            time.sleep(2)

    values = []
    for keyword in all_keywords:
        subcategory = mapped[keyword]
        root = subcategory_to_root[subcategory]
        values.append((keyword, root, subcategory))

    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()
    existing_embeddings = load_existing_embeddings(cur)
    cur.execute("DROP TABLE IF EXISTS keyword_taxonomy_map;")
    cur.execute("""
        CREATE TABLE keyword_taxonomy_map (
            canonical_keyword TEXT PRIMARY KEY,
            root_category TEXT NOT NULL,
            sub_category TEXT NOT NULL,
            embedding vector(768)
        );
        CREATE INDEX idx_taxonomy_root ON keyword_taxonomy_map(root_category);
        CREATE INDEX idx_taxonomy_sub ON keyword_taxonomy_map(sub_category);
    """)
    execute_values(
        cur,
        """
        INSERT INTO keyword_taxonomy_map
        (canonical_keyword, root_category, sub_category, embedding)
        VALUES %s
        """,
        [
            (keyword, root, subcategory, str(existing_embeddings[keyword]) if keyword in existing_embeddings else None)
            for keyword, root, subcategory in values
        ],
        template="(%s, %s, %s, %s::vector)",
        page_size=5000,
    )
    cur.close()
    conn.close()

    print(f"✅ keyword_taxonomy_map: {len(values)}")
    print(f"✅ embedding reuse: {len(existing_embeddings)}")
    print("📊 ilk 5 alt kategori:")
    for subcategory, count in Counter(mapped.values()).most_common(5):
        print(f"- {subcategory}: {count}")


if __name__ == "__main__":
    main()
