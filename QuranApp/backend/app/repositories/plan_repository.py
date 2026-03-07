"""
Plan repository — async database operations for plans and tasks.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from app.models.prescription import DailyPlan, PlanTask, Prescription


async def create_plan(
    db: AsyncSession,
    user_id,
    prescription_id,
    journey_title: str,
    journey_type: str,
    conversation_id=None,
    topic_summary: str = "",
    topic_keywords: list = None,
    total_days: int = 8,
) -> DailyPlan:
    """Create a new daily plan."""
    # Safely convert string IDs to UUID objects
    def to_uuid(val):
        if val is None:
            return None
        if isinstance(val, uuid.UUID):
            return val
        return uuid.UUID(str(val))

    plan = DailyPlan(
        user_id=to_uuid(user_id),
        prescription_id=to_uuid(prescription_id),
        conversation_id=to_uuid(conversation_id),
        journey_title=journey_title,
        journey_type=journey_type,
        topic_summary=topic_summary,
        topic_keywords=topic_keywords or [],
        total_days=total_days,
        current_day=0,
        status="active",
    )
    db.add(plan)
    await db.flush()  # Get ID before adding tasks
    return plan


async def add_task(
    db: AsyncSession,
    plan_id,
    day_number: int,
    task_type: str,
    title: str,
    description: str = "",
    duration_minutes: int = 5,
    order_index: int = 0,
    metadata: dict = None,
) -> PlanTask:
    """Add a task to a plan."""
    task = PlanTask(
        plan_id=plan_id,
        day_number=day_number,
        task_type=task_type,
        title=title,
        description=description,
        duration_minutes=duration_minutes,
        order_index=order_index,
        task_metadata=metadata,
    )
    db.add(task)
    return task


async def get_plan_by_id(db: AsyncSession, plan_id) -> Optional[DailyPlan]:
    """Get a plan by ID."""
    result = await db.execute(select(DailyPlan).where(DailyPlan.id == plan_id))
    return result.scalar_one_or_none()


async def get_plan_by_id_for_user(
    db: AsyncSession, plan_id, user_id
) -> Optional[DailyPlan]:
    """Get a plan by ID, scoped to a specific authenticated user."""
    uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
    result = await db.execute(
        select(DailyPlan).where(DailyPlan.id == plan_id, DailyPlan.user_id == uid)
    )
    return result.scalar_one_or_none()


async def get_anonymous_plan_by_id(db: AsyncSession, plan_id) -> Optional[DailyPlan]:
    """Get a plan by ID only if it belongs to an anonymous session."""
    result = await db.execute(
        select(DailyPlan).where(DailyPlan.id == plan_id, DailyPlan.user_id.is_(None))
    )
    return result.scalar_one_or_none()


async def get_plan_tasks(db: AsyncSession, plan_id) -> List[PlanTask]:
    """Get all tasks for a plan, ordered by day and index."""
    result = await db.execute(
        select(PlanTask)
        .where(PlanTask.plan_id == plan_id)
        .order_by(PlanTask.day_number, PlanTask.order_index)
    )
    return list(result.scalars().all())


async def get_user_plans(db: AsyncSession, user_id) -> List[DailyPlan]:
    """Get all plans for a user."""
    result = await db.execute(
        select(DailyPlan)
        .where(DailyPlan.user_id == user_id)
        .order_by(DailyPlan.started_at.desc())
    )
    return list(result.scalars().all())


async def complete_task(db: AsyncSession, task_id, plan_id=None) -> Optional[PlanTask]:
    """Toggle task completion."""
    query = select(PlanTask).where(PlanTask.id == task_id)
    if plan_id is not None:
        query = query.where(PlanTask.plan_id == plan_id)

    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if task:
        task.is_completed = not task.is_completed
        task.completed_at = datetime.now(timezone.utc) if task.is_completed else None
        await db.commit()
    return task


async def complete_day(db: AsyncSession, plan_id, day_number: int) -> Optional[DailyPlan]:
    """Mark a day as complete and advance to next day."""
    plan = await get_plan_by_id(db, plan_id)
    if plan and plan.current_day == day_number:
        if day_number < plan.total_days - 1:  # total_days=8, last day is 7
            plan.current_day = day_number + 1
        else:
            plan.status = "completed"
            plan.completed_at = datetime.now(timezone.utc)
        await db.commit()
    return plan


async def get_active_plans_with_progress(
    db: AsyncSession, user_id
) -> List[dict]:
    """Get all active plans for a user with today's task completion status."""
    uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id

    # Get active plans
    result = await db.execute(
        select(DailyPlan)
        .where(DailyPlan.user_id == uid, DailyPlan.status == "active")
        .order_by(DailyPlan.started_at.desc())
    )
    plans = list(result.scalars().all())

    now = datetime.now(timezone.utc)

    summaries = []
    for plan in plans:
        # Get today's tasks
        task_result = await db.execute(
            select(PlanTask)
            .where(
                PlanTask.plan_id == plan.id,
                PlanTask.day_number == plan.current_day,
            )
            .order_by(PlanTask.order_index)
        )
        today_tasks = list(task_result.scalars().all())

        completed = sum(1 for t in today_tasks if t.is_completed)
        total = len(today_tasks)

        # Calculate elapsed days and completion percentage
        started_at = plan.started_at
        days_elapsed = (now - started_at).days if started_at else 0
        max_day = max(plan.total_days - 1, 1)  # Avoid division by zero
        completion_pct = round((plan.current_day / max_day) * 100)

        # Get emotion/reason from linked prescription
        emotion_category = None
        if plan.prescription_id:
            presc_result = await db.execute(
                select(Prescription.emotion_category)
                .where(Prescription.id == plan.prescription_id)
            )
            emotion_category = presc_result.scalar_one_or_none()

        summaries.append({
            "plan_id": str(plan.id),
            "title": plan.journey_title or "Plan",
            "journey_type": plan.journey_type,
            "topic_summary": plan.topic_summary,
            "topic_keywords": plan.topic_keywords or [],
            "current_day": plan.current_day,
            "total_days": plan.total_days,
            "started_at": started_at.isoformat() if started_at else None,
            "days_elapsed": days_elapsed,
            "completion_pct": completion_pct,
            "emotion_category": emotion_category,
            "today_tasks": [
                {
                    "title": t.title,
                    "type": t.task_type,
                    "completed": t.is_completed,
                    "description": t.description,
                }
                for t in today_tasks
            ],
            "today_completed": completed,
            "today_total": total,
        })

    return summaries


async def skip_day0(db: AsyncSession, plan_id) -> Optional[DailyPlan]:
    """Skip Day 0 and advance to Day 1."""
    plan = await get_plan_by_id(db, plan_id)
    if plan and plan.current_day == 0:
        plan.current_day = 1
        plan.day0_skipped = True
        await db.commit()
    return plan


async def get_completed_days(db: AsyncSession, plan_id) -> set:
    """Return set of day numbers where ALL tasks are completed."""
    tasks = await get_plan_tasks(db, plan_id)

    # Group by day
    days_tasks = {}
    for task in tasks:
        if task.day_number not in days_tasks:
            days_tasks[task.day_number] = []
        days_tasks[task.day_number].append(task)

    # Find days where all tasks are completed
    completed = set()
    for day_num, day_tasks in days_tasks.items():
        if day_tasks and all(t.is_completed for t in day_tasks):
            completed.add(day_num)

    return completed


async def delete_tasks_for_days(db: AsyncSession, plan_id, day_numbers: List[int]) -> int:
    """Delete all tasks for specific days."""
    from sqlalchemy import delete

    stmt = delete(PlanTask).where(
        PlanTask.plan_id == plan_id,
        PlanTask.day_number.in_(day_numbers)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


def active_plans_to_context_str(plans: List[dict]) -> str:
    """
    Convert active plan summaries to a rich string for AI prompt injection.
    Includes creation reason, start date, elapsed time, and completion %.
    """
    if not plans:
        return "Aktif plan yok."

    lines = [f"AKTİF PLANLAR ({len(plans)} adet):"]

    for i, p in enumerate(plans, 1):
        # Header
        lines.append(f"")
        lines.append(f"📋 Plan {i}: \"{p['title']}\"")

        # Reason / cause
        topic = p.get('topic_summary', 'Bilinmiyor')
        emotion = p.get('emotion_category', '')
        if emotion:
            lines.append(f"   Sebep: {topic} (duygu: {emotion})")
        else:
            lines.append(f"   Sebep: {topic}")

        # Start date and elapsed time
        started_at = p.get('started_at')
        days_elapsed = p.get('days_elapsed', 0)
        if started_at:
            # Parse ISO date for display
            try:
                dt = datetime.fromisoformat(started_at)
                date_str = dt.strftime('%d %B %Y')
            except (ValueError, TypeError):
                date_str = 'Bilinmiyor'
            elapsed_str = _format_elapsed(days_elapsed)
            lines.append(f"   Başlangıç: {date_str} ({elapsed_str})")

        # Progress
        day_label = f"Gün {p['current_day']}/{p['total_days'] - 1}"
        if p['current_day'] == 0:
            day_label = "Gün 0 (Başlangıç)"
        completion_pct = p.get('completion_pct', 0)
        lines.append(f"   İlerleme: {day_label} (%{completion_pct} tamamlandı)")

        # Today's tasks
        task_parts = []
        for t in p.get("today_tasks", []):
            mark = "✅" if t["completed"] else "❌"
            task_parts.append(f"{mark} {t['title']}")

        if task_parts:
            completed = p.get('today_completed', 0)
            total = p.get('today_total', 0)
            lines.append(f"   Bugün: {', '.join(task_parts)} ({completed}/{total})")

    return "\n".join(lines)


def _format_elapsed(days: int) -> str:
    """Format elapsed days into human-readable Turkish string."""
    if days == 0:
        return "bugün başladı"
    elif days == 1:
        return "dün başladı"
    elif days < 7:
        return f"{days} gün önce başladı"
    elif days < 30:
        weeks = days // 7
        return f"{weeks} hafta önce başladı"
    else:
        months = days // 30
        return f"{months} ay önce başladı"
