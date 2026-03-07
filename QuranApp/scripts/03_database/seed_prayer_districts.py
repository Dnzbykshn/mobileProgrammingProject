"""
One-time seed: fetch all countries/states/districts from ezanvakti.imsakiyem.com
and insert into the prayer_districts table.

Run from project root:
    python scripts/03_database/seed_prayer_districts.py

After this script succeeds, the app no longer needs the external API at runtime.
"""

import os
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
import urllib.request
import json
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / "backend" / ".env")

DB_PARAMS = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     os.getenv("DB_PORT", "5432"),
    "database": os.getenv("DB_NAME", "deniz_quran_source"),
    "user":     os.getenv("DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD"),
}

BASE_URL = "https://ezanvakti.imsakiyem.com/api"
RATE_LIMIT_SLEEP = 0.5  # seconds between requests (well under 100/5min limit)


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_countries() -> list[dict]:
    data = get_json(f"{BASE_URL}/locations/countries")
    return data.get("data", [])


def fetch_states(country_id: str) -> list[dict]:
    time.sleep(RATE_LIMIT_SLEEP)
    data = get_json(f"{BASE_URL}/locations/states?countryId={country_id}")
    return data.get("data", [])


def fetch_districts(state_id: str) -> list[dict]:
    time.sleep(RATE_LIMIT_SLEEP)
    data = get_json(f"{BASE_URL}/locations/districts?stateId={state_id}")
    return data.get("data", [])


def main() -> None:
    if not DB_PARAMS["password"]:
        print("❌ DB_PASSWORD tanımlı değil.")
        sys.exit(1)

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    print("🌍 Ülkeler çekiliyor...")
    countries = fetch_countries()
    print(f"   {len(countries)} ülke bulundu")

    rows: list[tuple] = []
    total_districts = 0

    for country in countries:
        country_id   = country["_id"]
        country_name = country["name"]

        print(f"\n📍 {country_name} (id={country_id}) — şehirler çekiliyor...")
        try:
            states = fetch_states(country_id)
        except Exception as e:
            print(f"   ⚠️ Şehirler alınamadı: {e}")
            continue

        print(f"   {len(states)} şehir")

        for state in states:
            state_id   = state["_id"]
            state_name = state["name"]

            try:
                districts = fetch_districts(state_id)
            except Exception as e:
                print(f"   ⚠️ {state_name} ilçeleri alınamadı: {e}")
                continue

            for d in districts:
                rows.append((
                    d["_id"],        # district_id
                    d["name"],       # district_name
                    state_id,        # state_id
                    state_name,      # state_name
                    country_id,      # country_id
                    country_name,    # country_name
                ))

            total_districts += len(districts)
            print(f"   ✔ {state_name}: {len(districts)} ilçe  (toplam: {total_districts})")

    print(f"\n💾 {len(rows)} satır DB'ye yazılıyor...")
    execute_values(
        cur,
        """
        INSERT INTO prayer_districts
            (district_id, district_name, state_id, state_name, country_id, country_name)
        VALUES %s
        ON CONFLICT (district_id) DO UPDATE SET
            district_name = EXCLUDED.district_name,
            state_id      = EXCLUDED.state_id,
            state_name    = EXCLUDED.state_name,
            country_id    = EXCLUDED.country_id,
            country_name  = EXCLUDED.country_name
        """,
        rows,
    )
    conn.commit()
    cur.close()
    conn.close()

    print(f"\n✅ Tamamlandı! {len(rows)} ilçe kaydedildi.")
    print("ℹ️  Artık uygulama tamamen kendi DB'sine güveniyor.")


if __name__ == "__main__":
    main()
