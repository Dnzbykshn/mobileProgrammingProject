"""
Prescription endpoints — generate, history, detail.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.dependencies import get_db, get_current_user
from app.schemas.plan import PrescriptionGenerateRequest, PrescriptionResponse
from app.services.prescription_engine import PrescriptionEngine
from app.models.prescription import Prescription
from app.core.rate_limit import limiter

router = APIRouter()


@router.post("/generate", response_model=PrescriptionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def generate_prescription(
    request: Request,
    payload: PrescriptionGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a spiritual therapy prescription and save to DB."""
    engine = PrescriptionEngine(db)
    data = await engine.process_request(payload.message)

    # Save to DB
    prescription = Prescription(
        user_id=current_user.id if current_user else None,
        title=data["diagnosis"]["emotional_state"],
        description=data.get("advice", ""),
        emotion_category=data["diagnosis"]["emotional_state"],
        prescription_data=data,
    )
    db.add(prescription)
    await db.commit()
    await db.refresh(prescription)

    return PrescriptionResponse(
        id=str(prescription.id),
        title=prescription.title,
        description=prescription.description,
        emotion_category=prescription.emotion_category,
        prescription_data=prescription.prescription_data,
        created_at=prescription.created_at,
    )


@router.get("/", response_model=List[PrescriptionResponse])
async def get_prescriptions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get user's prescription history."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    query = (
        select(Prescription)
        .where(Prescription.user_id == current_user.id)
        .order_by(Prescription.created_at.desc())
        .limit(20)
    )

    result = await db.execute(query)
    prescriptions = result.scalars().all()

    return [
        PrescriptionResponse(
            id=str(p.id),
            title=p.title,
            description=p.description,
            emotion_category=p.emotion_category,
            prescription_data=p.prescription_data,
            created_at=p.created_at,
        )
        for p in prescriptions
    ]


@router.get("/{prescription_id}", response_model=PrescriptionResponse)
async def get_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a single prescription by ID."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    result = await db.execute(
        select(Prescription).where(
            Prescription.id == prescription_id,
            Prescription.user_id == current_user.id,
        )
    )
    prescription = result.scalar_one_or_none()

    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")

    return PrescriptionResponse(
        id=str(prescription.id),
        title=prescription.title,
        description=prescription.description,
        emotion_category=prescription.emotion_category,
        prescription_data=prescription.prescription_data,
        created_at=prescription.created_at,
    )
