"""
One-time seed: fetch all countries/states/districts from ezanvakti.imsakiyem.com
and insert into the prayer_districts table.

Run from project root:
    python scripts/database/prayer/seed_prayer_districts.py

After this script succeeds, the app no longer needs the external API at runtime.
"""

import os
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
import urllib.request
import urllib.error
import json
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

DB_PARAMS = {
    "host": os.getenv("DB_HOST") or os.getenv("APP_DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT") or os.getenv("APP_DB_PORT", "5432"),
    "database": os.getenv("DB_NAME") or os.getenv("APP_DB_NAME", "quranapp_app_clean"),
    "user": os.getenv("DB_USER") or os.getenv("APP_DB_USER", "admin"),
    "password": os.getenv("DB_PASSWORD") or os.getenv("APP_DB_PASSWORD"),
}

BASE_URL = "https://ezanvakti.imsakiyem.com/api"
RATE_LIMIT_SLEEP = 0.75
RETRY_LIMIT = 5


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    last_error: Exception | None = None
    for attempt in range(RETRY_LIMIT):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429 and attempt < RETRY_LIMIT - 1:
                sleep_seconds = RATE_LIMIT_SLEEP * (2 ** attempt)
                print(f"   ⏳ 429 rate limit, retrying in {sleep_seconds:.1f}s -> {url}")
                time.sleep(sleep_seconds)
                continue
            raise
        except Exception as exc:
            last_error = exc
            if attempt < RETRY_LIMIT - 1:
                sleep_seconds = RATE_LIMIT_SLEEP * (attempt + 1)
                print(f"   ⏳ geçici hata, retrying in {sleep_seconds:.1f}s -> {url}")
                time.sleep(sleep_seconds)
                continue
            raise
    if last_error is not None:
        raise last_error
    raise RuntimeError("Unexpected prayer district fetch error")


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
