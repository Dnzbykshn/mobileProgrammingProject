import os
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "quranapp_resources_clean"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432"),
}

TURKISH_FOLD = str.maketrans({
    "ç": "c",
    "ğ": "g",
    "ı": "i",
    "ö": "o",
    "ş": "s",
    "ü": "u",
    "Ç": "c",
    "Ğ": "g",
    "İ": "i",
    "I": "i",
    "Ö": "o",
    "Ş": "s",
    "Ü": "u",
})


def clean_keyword(value: str | None) -> str | None:
    if not value:
        return None
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("’", "'").replace("`", "'")
    value = re.sub(r"\s+", " ", value).strip(" -_/.,;:")
    return value or None


def build_group_key(value: str) -> str:
    folded = value.translate(TURKISH_FOLD).lower()
    folded = re.sub(r"[^a-z0-9]+", " ", folded)
    return re.sub(r"\s+", " ", folded).strip()


def display_score(value: str) -> tuple[int, int, int, str]:
    turkish_chars = sum(char in "çğıöşüÇĞİÖŞÜ" for char in value)
    uppercase_bonus = int(value[:1].isupper())
    return (turkish_chars, uppercase_bonus, -len(value), value)


def main() -> None:
    conn = psycopg2.connect(**DB_PARAMS)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("""
        SELECT id, unnest(keywords) AS raw_keyword
        FROM knowledge_units
        WHERE keywords IS NOT NULL;
    """)
    rows = cur.fetchall()
    print(f"📂 {len(rows)} keyword satırı okundu.")

    variants_by_group: dict[str, Counter[str]] = defaultdict(Counter)
    cleaned_rows: list[tuple[int, str, str]] = []

    for knowledge_unit_id, raw_keyword in rows:
        cleaned = clean_keyword(raw_keyword)
        if not cleaned:
            continue
        group_key = build_group_key(cleaned)
        if not group_key:
            continue
        variants_by_group[group_key][cleaned] += 1
        cleaned_rows.append((knowledge_unit_id, cleaned, group_key))

    canonical_by_group: dict[str, str] = {}
    for group_key, variants in variants_by_group.items():
        canonical_by_group[group_key] = max(
            variants.items(),
            key=lambda item: (item[1],) + display_score(item[0]),
        )[0]

    raw_to_canonical = {
        raw_keyword: canonical_by_group[group_key]
        for _, raw_keyword, group_key in cleaned_rows
    }
    relation_rows = sorted({
        (knowledge_unit_id, canonical_by_group[group_key])
        for knowledge_unit_id, _, group_key in cleaned_rows
    })

    cur.execute("DROP TABLE IF EXISTS knowledge_units_graph_keywords;")
    cur.execute("DROP TABLE IF EXISTS keyword_canonical_map;")

    cur.execute("""
        CREATE TABLE keyword_canonical_map (
            raw_keyword TEXT PRIMARY KEY,
            canonical_keyword TEXT NOT NULL
        );
        CREATE INDEX idx_keyword_canonical_map_canonical
        ON keyword_canonical_map (canonical_keyword);
    """)

    cur.execute("""
        CREATE TABLE knowledge_units_graph_keywords (
            knowledge_unit_id INTEGER NOT NULL REFERENCES knowledge_units(id) ON DELETE CASCADE,
            canonical_keyword TEXT NOT NULL,
            PRIMARY KEY (knowledge_unit_id, canonical_keyword)
        );
        CREATE INDEX idx_knowledge_units_graph_keywords_keyword
        ON knowledge_units_graph_keywords (canonical_keyword);
    """)

    execute_values(
        cur,
        "INSERT INTO keyword_canonical_map (raw_keyword, canonical_keyword) VALUES %s",
        sorted(raw_to_canonical.items()),
        page_size=5000,
    )
    execute_values(
        cur,
        """
        INSERT INTO knowledge_units_graph_keywords (knowledge_unit_id, canonical_keyword)
        VALUES %s
        """,
        relation_rows,
        page_size=5000,
    )

    cur.execute("SELECT COUNT(DISTINCT canonical_keyword) FROM knowledge_units_graph_keywords;")
    distinct_canonical = cur.fetchone()[0]

    print(f"✅ keyword_canonical_map: {len(raw_to_canonical)}")
    print(f"✅ knowledge_units_graph_keywords: {len(relation_rows)}")
    print(f"✅ distinct canonical keyword: {distinct_canonical}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
