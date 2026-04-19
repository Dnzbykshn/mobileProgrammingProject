from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


UPSTREAM_PRAYER_API_BASE_URL = "https://ezanvakti.imsakiyem.com/api"


@dataclass(frozen=True)
class PrayerTimeRecord:
    district_id: str
    day: date
    imsak: str
    gunes: str
    ogle: str
    ikindi: str
    aksam: str
    yatsi: str
    hijri_day: int | None
    hijri_month: int | None
    hijri_month_name: str | None
    hijri_year: int | None


class PrayerTimesSyncService:
    """Fetches prayer times from the upstream public API and caches them locally.

    The clean stack should be usable even if the bulk prayer time import file is
    not available. Districts are seeded once into the app DB, then prayer times
    are lazily synced on demand and stored in `prayer_times`.
    """

    async def ensure_range(
        self,
        db: AsyncSession,
        *,
        district_id: str,
        from_date: date,
        to_date: date,
    ) -> None:
        if from_date > to_date:
            return

        missing_count = await self._count_missing_days(
            db,
            district_id=district_id,
            from_date=from_date,
            to_date=to_date,
        )
        if missing_count == 0:
            return

        records = await self._fetch_upstream(
            district_id=district_id,
            from_date=from_date,
            to_date=to_date,
        )
        if not records:
            return

        await self._upsert_records(db, records)

    async def _count_missing_days(
        self,
        db: AsyncSession,
        *,
        district_id: str,
        from_date: date,
        to_date: date,
    ) -> int:
        result = await db.execute(
            text(
                """
                SELECT ((CAST(:to_date AS date) - CAST(:from_date AS date)) + 1) - COUNT(*) AS missing_count
                FROM prayer_times
                WHERE district_id = :district_id
                  AND date BETWEEN :from_date AND :to_date
                """
            ),
            {
                "district_id": district_id,
                "from_date": from_date,
                "to_date": to_date,
            },
        )
        return max(int(result.scalar_one() or 0), 0)

    async def _upsert_records(self, db: AsyncSession, records: list[PrayerTimeRecord]) -> None:
        values = [
            {
                "district_id": item.district_id,
                "date": item.day,
                "imsak": item.imsak,
                "gunes": item.gunes,
                "ogle": item.ogle,
                "ikindi": item.ikindi,
                "aksam": item.aksam,
                "yatsi": item.yatsi,
                "hijri_day": item.hijri_day,
                "hijri_month": item.hijri_month,
                "hijri_month_name": item.hijri_month_name,
                "hijri_year": item.hijri_year,
            }
            for item in records
        ]

        stmt = text(
            """
            INSERT INTO prayer_times (
                district_id, date, imsak, gunes, ogle, ikindi, aksam, yatsi,
                hijri_day, hijri_month, hijri_month_name, hijri_year
            ) VALUES (
                :district_id, :date, :imsak, :gunes, :ogle, :ikindi, :aksam, :yatsi,
                :hijri_day, :hijri_month, :hijri_month_name, :hijri_year
            )
            ON CONFLICT (district_id, date) DO UPDATE SET
                imsak = EXCLUDED.imsak,
                gunes = EXCLUDED.gunes,
                ogle = EXCLUDED.ogle,
                ikindi = EXCLUDED.ikindi,
                aksam = EXCLUDED.aksam,
                yatsi = EXCLUDED.yatsi,
                hijri_day = EXCLUDED.hijri_day,
                hijri_month = EXCLUDED.hijri_month,
                hijri_month_name = EXCLUDED.hijri_month_name,
                hijri_year = EXCLUDED.hijri_year
            """
        )
        await db.execute(stmt, values)
        await db.commit()

    async def _fetch_upstream(
        self,
        *,
        district_id: str,
        from_date: date,
        to_date: date,
    ) -> list[PrayerTimeRecord]:
        period = self._resolve_period(from_date=from_date, to_date=to_date)
        query = urlencode(
            {
                "startDate": from_date.isoformat(),
                "endDate": to_date.isoformat(),
            }
        )
        url = f"{UPSTREAM_PRAYER_API_BASE_URL}/prayer-times/{district_id}/{period}?{query}"
        payload = await self._get_json(url)
        raw_items = payload.get("data") or []
        return [self._map_item(item) for item in raw_items]

    @staticmethod
    def _resolve_period(*, from_date: date, to_date: date) -> str:
        total_days = (to_date - from_date).days + 1
        if total_days <= 1:
            return "daily"
        if total_days <= 8:
            return "weekly"
        if total_days <= 31:
            return "monthly"
        return "yearly"

    @staticmethod
    async def _get_json(url: str) -> dict[str, Any]:
        def _sync_get() -> dict[str, Any]:
            request = Request(url, headers={"Accept": "application/json"})
            with urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode())

        import asyncio

        return await asyncio.to_thread(_sync_get)

    @staticmethod
    def _map_item(item: dict[str, Any]) -> PrayerTimeRecord:
        times = item.get("times") or {}
        hijri = item.get("hijri_date") or {}
        district = item.get("district_id") or {}
        return PrayerTimeRecord(
            district_id=str(district.get("_id") or item.get("district_id") or ""),
            day=date.fromisoformat(str(item.get("date", ""))[:10]),
            imsak=str(times.get("imsak") or ""),
            gunes=str(times.get("gunes") or ""),
            ogle=str(times.get("ogle") or ""),
            ikindi=str(times.get("ikindi") or ""),
            aksam=str(times.get("aksam") or ""),
            yatsi=str(times.get("yatsi") or ""),
            hijri_day=hijri.get("day"),
            hijri_month=hijri.get("month"),
            hijri_month_name=hijri.get("month_name"),
            hijri_year=hijri.get("year"),
        )
