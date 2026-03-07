import psycopg2
import os
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(r"c:\Users\deniz\Desktop\QuranApp")
load_dotenv(PROJECT_ROOT / ".env")

DB_PARAMS = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "islamic_knowledge_source"),
    "user": os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", "5432")
}

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()
cur.execute("SELECT canonical_keyword, sub_category, root_category FROM keyword_taxonomy_map WHERE root_category = 'Uncategorized';")
rows = cur.fetchall()
print(f"Uyarı alan / Uydurulan Kategori Sayısı: {len(rows)}")
for r in rows:
    print(r)
cur.close()
conn.close()
