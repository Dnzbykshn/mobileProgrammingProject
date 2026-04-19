"""
Location endpoints — served entirely from the local prayer_districts table.
No external API calls at runtime.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db

router = APIRouter()

EXCLUDED_COUNTRY_IDS = {"1216"}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class Country(BaseModel):
    id: str
    name: str


class State(BaseModel):
    id: str
    name: str
    country_id: str


class District(BaseModel):
    id: str
    name: str
    state_id: str
    state_name: str
    country_id: str
    country_name: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/countries", response_model=List[Country])
async def list_countries(db: AsyncSession = Depends(get_db)):
    """Return all countries that have prayer time data."""
    result = await db.execute(
        text("""
            SELECT DISTINCT country_id, country_name
            FROM prayer_districts
            WHERE country_id != :excluded_country_id
            ORDER BY country_name
        """),
        {"excluded_country_id": next(iter(EXCLUDED_COUNTRY_IDS))},
    )
    rows = result.fetchall()
    # Put TR and KKTC first
    priority = {"2": 0, "1": 1}  # 2=TÜRKİYE, 1=KUZEY KIBRIS
    sorted_rows = sorted(rows, key=lambda r: (priority.get(r.country_id, 99), r.country_name))
    return [Country(id=r.country_id, name=r.country_name) for r in sorted_rows]


@router.get("/states", response_model=List[State])
async def list_states(
    country_id: str = Query(..., description="Country ID, e.g. 2 for Türkiye"),
    db: AsyncSession = Depends(get_db),
):
    """Return all states/cities for a country."""
    result = await db.execute(
        text("""
            SELECT DISTINCT state_id, state_name, country_id
            FROM prayer_districts
            WHERE country_id = :country_id
            ORDER BY state_name
        """),
        {"country_id": country_id},
    )
    rows = result.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No states found for country '{country_id}'")
    return [State(id=r.state_id, name=r.state_name, country_id=r.country_id) for r in rows]


@router.get("/districts", response_model=List[District])
async def list_districts(
    state_id: str = Query(..., description="State ID, e.g. 539 for İstanbul"),
    db: AsyncSession = Depends(get_db),
):
    """Return all districts for a state."""
    result = await db.execute(
        text("""
            SELECT district_id, district_name, state_id, state_name, country_id, country_name
            FROM prayer_districts
            WHERE state_id = :state_id
            ORDER BY district_name
        """),
        {"state_id": state_id},
    )
    rows = result.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No districts found for state '{state_id}'")
    return [
        District(
            id=r.district_id,
            name=r.district_name,
            state_id=r.state_id,
            state_name=r.state_name,
            country_id=r.country_id,
            country_name=r.country_name,
        )
        for r in rows
    ]


@router.get("/district/{district_id}", response_model=District)
async def get_district(
    district_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Return district details by ID."""
    result = await db.execute(
        text("""
            SELECT district_id, district_name, state_id, state_name, country_id, country_name
            FROM prayer_districts
            WHERE district_id = :district_id
        """),
        {"district_id": district_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"District '{district_id}' not found")
    return District(
        id=row.district_id,
        name=row.district_name,
        state_id=row.state_id,
        state_name=row.state_name,
        country_id=row.country_id,
        country_name=row.country_name,
    )


@router.get("/search", response_model=List[District])
async def search_districts(
    q: str = Query(..., min_length=2, description="Search query"),
    country_id: Optional[str] = Query(None, description="Filter by country ID"),
    db: AsyncSession = Depends(get_db),
):
    """Full-text search across district and state names."""
    query = f"%{q.upper()}%"
    sql = """
        SELECT district_id, district_name, state_id, state_name, country_id, country_name
        FROM prayer_districts
        WHERE (district_name ILIKE :q OR state_name ILIKE :q)
    """
    params: dict = {"q": query}
    if country_id:
        sql += " AND country_id = :country_id"
        params["country_id"] = country_id
    sql += " ORDER BY district_name LIMIT 50"

    result = await db.execute(text(sql), params)
    return [
        District(
            id=r.district_id,
            name=r.district_name,
            state_id=r.state_id,
            state_name=r.state_name,
            country_id=r.country_id,
            country_name=r.country_name,
        )
        for r in result.fetchall()
    ]
