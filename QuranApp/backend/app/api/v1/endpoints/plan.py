"""
Plan endpoints — 7-day journey management.
Matches mobile app's plan.tsx UI.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.schemas.plan import (
    PlanCreateRequest, PlanResponse, DayGroup, TaskResponse, DayCompleteRequest, JourneySummary,
)
from app.services.plan_service import PlanService
from app.repositories import plan_repository

router = APIRouter()


def _parse_plan_id_or_400(plan_id: str) -> UUID:
    try:
        return UUID(plan_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan ID format")


async def _get_authorized_plan_or_404(db: AsyncSession, plan_id: str, current_user):
    plan_uuid = _parse_plan_id_or_400(plan_id)

    if current_user:
        plan = await plan_repository.get_plan_by_id_for_user(db, plan_uuid, current_user.id)
    else:
        plan = await plan_repository.get_anonymous_plan_by_id(db, plan_uuid)

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/create", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    request: PlanCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate a personalized 8-day journey using AI."""
    service = PlanService(db)
    plan = await service.create_journey(
        user_id=current_user.id if current_user else None,
        prescription_id=request.prescription_id,
        journey_type=request.journey_type,
        user_context=request.user_input or "",
    )
    # Fetch with tasks for response
    result = await service.get_plan_with_tasks(plan.id)
    if not result:
        raise HTTPException(status_code=500, detail="Plan creation failed")

    plan, days_map = result
    return _format_plan_response(plan, days_map)

# Valid endpoints (specific paths) must be defined BEFORE the generic /{plan_id} endpoint.
@router.post("/{plan_id}/days/0/skip")
async def skip_day0(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Skip Day 0 and advance to Day 1."""
    authorized_plan = await _get_authorized_plan_or_404(db, plan_id, current_user)
    plan = await plan_repository.skip_day0(db, authorized_plan.id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "plan_id": str(plan.id),
        "current_day": plan.current_day,
        "message": "Gün 0 atlandı, Gün 1'e geçildi.",
    }


@router.get("/active", response_model=List[JourneySummary])
async def get_active_journeys(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all active journeys for the current user."""
    if not current_user:
        return []

    plans = await plan_repository.get_active_plans_with_progress(db, current_user.id)
    return [
        JourneySummary(
            plan_id=str(p["plan_id"]),
            title=p["title"],
            journey_type=p["journey_type"],
            topic_summary=p.get("topic_summary"),
            current_day=p["current_day"],
            total_days=p["total_days"],
            status="active",
            today_completed=p["today_completed"],
            today_total=p["today_total"],
            started_at=None,
        )
        for p in plans
    ]

@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get plan with all tasks grouped by day."""
    authorized_plan = await _get_authorized_plan_or_404(db, plan_id, current_user)

    service = PlanService(db)
    result = await service.get_plan_with_tasks(authorized_plan.id)
    if not result:
        raise HTTPException(status_code=404, detail="Plan not found")

    plan, days_map = result
    return _format_plan_response(plan, days_map)


@router.put("/{plan_id}/tasks/{task_id}/complete")
async def toggle_task(
    plan_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Toggle a task's completion status."""
    authorized_plan = await _get_authorized_plan_or_404(db, plan_id, current_user)

    service = PlanService(db)
    task = await service.complete_task(task_id, plan_id=authorized_plan.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": str(task.id),
        "is_completed": task.is_completed,
        "completed_at": str(task.completed_at) if task.completed_at else None,
    }


@router.post("/{plan_id}/days/{day_number}/complete")
async def complete_day(
    plan_id: str,
    day_number: int,
    body: DayCompleteRequest = DayCompleteRequest(),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Complete a day and unlock the next."""
    authorized_plan = await _get_authorized_plan_or_404(db, plan_id, current_user)

    service = PlanService(db)
    plan = await service.complete_day(authorized_plan.id, day_number)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return {
        "plan_id": str(plan.id),
        "current_day": plan.current_day,
        "status": plan.status,
        "message": "Tebrikler! Bir sonraki güne geçtiniz." if plan.status == "active" else "Yolculuk tamamlandı! 🎉",
    }






def _format_plan_response(plan, days_map: dict) -> PlanResponse:
    """Helper to format plan + tasks into the response schema."""
    day_groups = []
    for day_num in sorted(days_map.keys()):
        tasks = days_map[day_num]
        task_responses = [
            TaskResponse(
                id=str(t.id),
                day_number=t.day_number,
                task_type=t.task_type,
                title=t.title,
                description=t.description,
                duration_minutes=t.duration_minutes,
                order_index=t.order_index,
                is_completed=t.is_completed,
                completed_at=t.completed_at,
                task_metadata=t.task_metadata,
            )
            for t in tasks
        ]
        is_complete = all(t.is_completed for t in tasks)
        is_day0 = day_num == 0
        day_groups.append(
            DayGroup(
                day_number=day_num,
                tasks=task_responses,
                is_complete=is_complete,
                is_day0=is_day0,
                is_skippable=is_day0,
            )
        )

    return PlanResponse(
        id=str(plan.id),
        journey_title=plan.journey_title or "",
        journey_type=plan.journey_type or "",
        total_days=plan.total_days,
        current_day=plan.current_day,
        status=plan.status,
        started_at=plan.started_at,
        days=day_groups,
        topic_summary=plan.topic_summary,
        day0_skipped=plan.day0_skipped,
    )
