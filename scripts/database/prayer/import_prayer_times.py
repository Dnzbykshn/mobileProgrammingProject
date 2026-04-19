"""
Import prayer times from prayer-times.2026.json into PostgreSQL.

Usage (run from project root):
    python scripts/database/prayer/import_prayer_times.py

Requirements:
    pip install psycopg2-binary python-dotenv

The script is idempotent — re-running it won't create duplicate rows
because the table has a UNIQUE constraint on (district_id, date).
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"
DATA_FILE = PROJECT_ROOT / "data" / "prayer-times.2026.json"

load_dotenv(ENV_FILE)

DB_PARAMS = {
    "host": os.getenv("DB_HOST") or os.getenv("APP_DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT") or os.getenv("APP_DB_PORT", "5432"),
    "database": os.getenv("DB_NAME") or os.getenv("APP_DB_NAME", "quranapp_app_clean"),
    "user": os.getenv("DB_USER") or os.getenv("APP_DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD") or os.getenv("APP_DB_PASSWORD"),
}

BATCH_SIZE = 5_000  # rows per INSERT batch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_date(iso_str: str) -> date:
    """'2026-01-01T00:00:00.000Z' → date(2026, 1, 1)"""
    return date.fromisoformat(iso_str[:10])


def build_row(record: dict) -> tuple:
    """Convert a single JSON record into a DB row tuple."""
    h = record.get("hijri_date", {})
    t = record["times"]
    return (
        record["district_id"],
        parse_date(record["date"]),
        t["imsak"],
        t["gunes"],
        t["ogle"],
        t["ikindi"],
        t["aksam"],
        t["yatsi"],
        h.get("day"),
        h.get("month"),
        h.get("month_name"),
        h.get("year"),
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not DB_PARAMS["password"]:
        print("❌ DB_PASSWORD ortam değişkeni tanımlı değil. .env dosyanızı kontrol edin.")
        sys.exit(1)

    print(f"📂 Dosya okunuyor: {DATA_FILE}")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        payload = json.load(f)

    records = payload["data"]
    total = len(records)
    print(f"📊 Toplam kayıt: {total:,}  |  İlçe sayısı: {payload['meta']['total_districts']}")

    print(f"🔌 PostgreSQL'e bağlanılıyor → {DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}")
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    # Ensure table exists (migration should have run, but just in case)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS prayer_times (
            id            SERIAL PRIMARY KEY,
            district_id   VARCHAR(20)  NOT NULL,
            date          DATE         NOT NULL,
            imsak         VARCHAR(5)   NOT NULL,
            gunes         VARCHAR(5)   NOT NULL,
            ogle          VARCHAR(5)   NOT NULL,
            ikindi        VARCHAR(5)   NOT NULL,
            aksam         VARCHAR(5)   NOT NULL,
            yatsi         VARCHAR(5)   NOT NULL,
            hijri_day     SMALLINT,
            hijri_month   SMALLINT,
            hijri_month_name VARCHAR(30),
            hijri_year    SMALLINT,
            CONSTRAINT uq_prayer_district_date UNIQUE (district_id, date)
        );
        CREATE INDEX IF NOT EXISTS ix_prayer_times_district_date
            ON prayer_times (district_id, date);
    """)
    conn.commit()

    INSERT_SQL = """
        INSERT INTO prayer_times
            (district_id, date, imsak, gunes, ogle, ikindi, aksam, yatsi,
             hijri_day, hijri_month, hijri_month_name, hijri_year)
        VALUES %s
        ON CONFLICT (district_id, date) DO NOTHING
    """

    inserted = 0
    skipped = 0
    batch: list[tuple] = []

    for i, record in enumerate(records, start=1):
        batch.append(build_row(record))

        if len(batch) >= BATCH_SIZE:
            execute_values(cur, INSERT_SQL, batch)
            conn.commit()
            inserted += len(batch)
            batch = []
            pct = (i / total) * 100
            print(f"   💾 {i:>7,} / {total:,}  ({pct:.1f}%)  inserted so far: {inserted:,}")

    # Final partial batch
    if batch:
        execute_values(cur, INSERT_SQL, batch)
        conn.commit()
        inserted += len(batch)

    cur.close()
    conn.close()

    print(f"\n✅ Tamamlandı! {inserted:,} kayıt eklendi.")
    print("ℹ️  Tekrar çalıştırırsanız ON CONFLICT DO NOTHING ile güvenle atlayacak.")


if __name__ == "__main__":
    main()
