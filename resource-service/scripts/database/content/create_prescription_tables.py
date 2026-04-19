import os
from pathlib import Path

import psycopg2
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


def create_tables() -> None:
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    print("🛠️ Prescription tabloları oluşturuluyor...")

    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS esma_ul_husna (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            appellation VARCHAR(100),
            meaning TEXT,
            psychological_benefits TEXT[],
            referral_note TEXT,
            embedding vector(768)
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS prophet_duas (
            id SERIAL PRIMARY KEY,
            source VARCHAR(100),
            arabic_text TEXT,
            turkish_text TEXT,
            context TEXT,
            emotional_tags TEXT[],
            embedding vector(768)
        );
    """)

    cur.execute("""
        CREATE INDEX IF NOT EXISTS esma_embedding_idx
        ON esma_ul_husna USING hnsw (embedding vector_cosine_ops);
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS dua_embedding_idx
        ON prophet_duas USING hnsw (embedding vector_cosine_ops);
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Prescription tabloları hazır.")


if __name__ == "__main__":
    create_tables()
