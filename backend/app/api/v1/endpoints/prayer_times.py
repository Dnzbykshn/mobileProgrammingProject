"""
Prayer Times endpoints.
Serves Diyanet prayer times stored in the prayer_times table.
"""
from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.services.prayer_times_sync_service import PrayerTimesSyncService

router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class HijriDate(BaseModel):
    day: Optional[int]
    month: Optional[int]
    month_name: Optional[str]
    year: Optional[int]


class PrayerTimesDay(BaseModel):
    date: date
    district_id: str
    imsak: str
    gunes: str
    ogle: str
    ikindi: str
    aksam: str
    yatsi: str
    hijri: HijriDate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _fetch_times(
    db: AsyncSession,
    district_id: str,
    from_date: date,
    to_date: date,
) -> List[PrayerTimesDay]:
    result = await db.execute(
        text("""
            SELECT date, district_id,
                   imsak, gunes, ogle, ikindi, aksam, yatsi,
                   hijri_day, hijri_month, hijri_month_name, hijri_year
            FROM prayer_times
            WHERE district_id = :district_id
              AND date BETWEEN :from_date AND :to_date
            ORDER BY date
        """),
        {"district_id": district_id, "from_date": from_date, "to_date": to_date},
    )
    rows = result.fetchall()
    return [
        PrayerTimesDay(
            date=row.date,
            district_id=row.district_id,
            imsak=row.imsak,
            gunes=row.gunes,
            ogle=row.ogle,
            ikindi=row.ikindi,
            aksam=row.aksam,
            yatsi=row.yatsi,
            hijri=HijriDate(
                day=row.hijri_day,
                month=row.hijri_month,
                month_name=row.hijri_month_name,
                year=row.hijri_year,
            ),
        )
        for row in rows
    ]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/today", response_model=PrayerTimesDay)
async def get_today(
    district_id: str = Query(..., description="Diyanet district ID, e.g. 15153"),
    db: AsyncSession = Depends(get_db),
):
    """Return prayer times for today for the given district."""
    today = date.today()
    results = await _fetch_times(db, district_id, today, today)
    if not results:
        await PrayerTimesSyncService().ensure_range(
            db,
            district_id=district_id,
            from_date=today,
            to_date=today,
        )
        results = await _fetch_times(db, district_id, today, today)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No prayer times found for district '{district_id}' on {today}.",
        )
    return results[0]


@router.get("/week", response_model=List[PrayerTimesDay])
async def get_week(
    district_id: str = Query(..., description="Diyanet district ID, e.g. 15153"),
    db: AsyncSession = Depends(get_db),
):
    """Return prayer times for the next 7 days for the given district."""
    today = date.today()
    end = today + timedelta(days=6)
    results = await _fetch_times(db, district_id, today, end)
    if len(results) < 7:
        await PrayerTimesSyncService().ensure_range(
            db,
            district_id=district_id,
            from_date=today,
            to_date=end,
        )
        results = await _fetch_times(db, district_id, today, end)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No prayer times found for district '{district_id}'.",
        )
    return results


@router.get("/date", response_model=PrayerTimesDay)
async def get_by_date(
    district_id: str = Query(..., description="Diyanet district ID, e.g. 15153"),
    on: date = Query(..., description="Date in YYYY-MM-DD format"),
    db: AsyncSession = Depends(get_db),
):
    """Return prayer times for a specific date and district."""
    results = await _fetch_times(db, district_id, on, on)
    if not results:
        await PrayerTimesSyncService().ensure_range(
            db,
            district_id=district_id,
            from_date=on,
            to_date=on,
        )
        results = await _fetch_times(db, district_id, on, on)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No prayer times found for district '{district_id}' on {on}.",
        )
    return results[0]


@router.get("/districts", response_model=List[str])
async def list_districts(db: AsyncSession = Depends(get_db)):
    """Return all available district IDs."""
    result = await db.execute(
        text("SELECT DISTINCT district_id FROM prayer_times ORDER BY district_id")
    )
    return [row[0] for row in result.fetchall()]
