"""Pathway repository.

Single database access module for pathways and pathway tasks.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pathway import Pathway, PathwayTask


def _to_uuid(value):
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


async def create_pathway(
    db: AsyncSession,
    user_id,
    title: str,
    pathway_type: str,
    conversation_id=None,
    topic_summary: str = "",
    topic_keywords: list[str] | None = None,
    total_days: int = 8,
) -> Pathway:
    pathway = Pathway(
        user_id=_to_uuid(user_id),
        conversation_id=_to_uuid(conversation_id),
        title=title,
        pathway_type=pathway_type,
        topic_summary=topic_summary,
        topic_keywords=topic_keywords or [],
        total_days=total_days,
        current_day=0,
        status="active",
    )
    db.add(pathway)
    await db.flush()
    return pathway


async def add_pathway_task(
    db: AsyncSession,
    pathway_id,
    day_number: int,
    task_type: str,
    title: str,
    description: str = "",
    duration_minutes: int = 5,
    order_index: int = 0,
    metadata: dict | None = None,
) -> PathwayTask:
    task = PathwayTask(
        pathway_id=pathway_id,
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


async def get_pathway_by_id(db: AsyncSession, pathway_id) -> Optional[Pathway]:
    result = await db.execute(select(Pathway).where(Pathway.id == pathway_id))
    return result.scalar_one_or_none()


async def get_pathway_by_id_for_user(db: AsyncSession, pathway_id, user_id) -> Optional[Pathway]:
    uid = _to_uuid(user_id)
    result = await db.execute(
        select(Pathway).where(Pathway.id == pathway_id, Pathway.user_id == uid)
    )
    return result.scalar_one_or_none()


async def get_anonymous_pathway_by_id(db: AsyncSession, pathway_id) -> Optional[Pathway]:
    result = await db.execute(
        select(Pathway).where(Pathway.id == pathway_id, Pathway.user_id.is_(None))
    )
    return result.scalar_one_or_none()


async def get_pathway_tasks(db: AsyncSession, pathway_id) -> list[PathwayTask]:
    result = await db.execute(
        select(PathwayTask)
        .where(PathwayTask.pathway_id == pathway_id)
        .order_by(PathwayTask.day_number, PathwayTask.order_index)
    )
    return list(result.scalars().all())


async def get_pathway_task_by_id(db: AsyncSession, pathway_id, task_id) -> Optional[PathwayTask]:
    result = await db.execute(
        select(PathwayTask).where(
            PathwayTask.pathway_id == pathway_id,
            PathwayTask.id == task_id,
        )
    )
    return result.scalar_one_or_none()


async def get_user_pathways(db: AsyncSession, user_id) -> list[Pathway]:
    uid = _to_uuid(user_id)
    result = await db.execute(
        select(Pathway)
        .where(Pathway.user_id == uid)
        .order_by(Pathway.started_at.desc())
    )
    return list(result.scalars().all())


async def toggle_task_completion(db: AsyncSession, task_id, pathway_id=None) -> Optional[PathwayTask]:
    query = select(PathwayTask).where(PathwayTask.id == task_id)
    if pathway_id is not None:
        query = query.where(PathwayTask.pathway_id == pathway_id)

    result = await db.execute(query)
    task = result.scalar_one_or_none()
    if task:
        task.is_completed = not task.is_completed
        task.completed_at = datetime.now(timezone.utc) if task.is_completed else None
        await db.commit()
    return task


async def complete_pathway_day(db: AsyncSession, pathway_id, day_number: int) -> Optional[Pathway]:
    pathway = await get_pathway_by_id(db, pathway_id)
    if pathway and pathway.current_day == day_number:
        if day_number < pathway.total_days - 1:
            pathway.current_day = day_number + 1
        else:
            pathway.status = "completed"
            pathway.completed_at = datetime.now(timezone.utc)
        await db.commit()
    return pathway


async def get_active_pathways_with_progress(db: AsyncSession, user_id) -> list[dict]:
    uid = _to_uuid(user_id)

    result = await db.execute(
        select(Pathway)
        .where(Pathway.user_id == uid, Pathway.status == "active")
        .order_by(Pathway.started_at.desc())
    )
    pathways = list(result.scalars().all())

    now = datetime.now(timezone.utc)
    summaries = []
    for pathway in pathways:
        task_result = await db.execute(
            select(PathwayTask)
            .where(
                PathwayTask.pathway_id == pathway.id,
                PathwayTask.day_number == pathway.current_day,
            )
            .order_by(PathwayTask.order_index)
        )
        today_tasks = list(task_result.scalars().all())

        completed = sum(1 for task in today_tasks if task.is_completed)
        total = len(today_tasks)

        started_at = pathway.started_at
        days_elapsed = (now - started_at).days if started_at else 0
        max_day = max(pathway.total_days - 1, 1)
        completion_pct = round((pathway.current_day / max_day) * 100)

        emotion_category = None

        summaries.append(
            {
                "pathway_id": str(pathway.id),
                "title": pathway.title or "Yol",
                "pathway_type": pathway.pathway_type,
                "topic_summary": pathway.topic_summary,
                "topic_keywords": pathway.topic_keywords or [],
                "current_day": pathway.current_day,
                "total_days": pathway.total_days,
                "started_at": started_at.isoformat() if started_at else None,
                "days_elapsed": days_elapsed,
                "completion_pct": completion_pct,
                "emotion_category": emotion_category,
                "today_tasks": [
                    {
                        "title": task.title,
                        "type": task.task_type,
                        "completed": task.is_completed,
                        "description": task.description,
                    }
                    for task in today_tasks
                ],
                "today_completed": completed,
                "today_total": total,
            }
        )

    return summaries


async def skip_pathway_day0(db: AsyncSession, pathway_id) -> Optional[Pathway]:
    pathway = await get_pathway_by_id(db, pathway_id)
    if pathway and pathway.current_day == 0:
        pathway.current_day = 1
        pathway.day0_skipped = True
        await db.commit()
    return pathway


async def get_completed_pathway_days(db: AsyncSession, pathway_id) -> set:
    tasks = await get_pathway_tasks(db, pathway_id)

    grouped_tasks: dict[int, list[PathwayTask]] = {}
    for task in tasks:
        grouped_tasks.setdefault(task.day_number, []).append(task)

    completed_days = set()
    for day_number, day_tasks in grouped_tasks.items():
        if day_tasks and all(task.is_completed for task in day_tasks):
            completed_days.add(day_number)

    return completed_days


async def delete_tasks_for_pathway_days(db: AsyncSession, pathway_id, day_numbers: list[int]) -> int:
    stmt = delete(PathwayTask).where(
        PathwayTask.pathway_id == pathway_id,
        PathwayTask.day_number.in_(day_numbers),
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


def active_pathways_to_context_str(pathways: list[dict]) -> str:
    if not pathways:
        return "Aktif yol yok."

    lines = [f"AKTİF YOLLAR ({len(pathways)} adet):"]
    for index, pathway in enumerate(pathways, start=1):
        lines.append("")
        lines.append(f"🛤️ Yol {index}: \"{pathway['title']}\"")

        topic = pathway.get("topic_summary", "Bilinmiyor")
        emotion = pathway.get("emotion_category", "")
        if emotion:
            lines.append(f"   Odak: {topic} (duygu: {emotion})")
        else:
            lines.append(f"   Odak: {topic}")

        started_at = pathway.get("started_at")
        days_elapsed = pathway.get("days_elapsed", 0)
        if started_at:
            lines.append(f"   Başlangıç: {started_at} ({_format_elapsed(days_elapsed)})")

        day_label = f"Gün {pathway['current_day']}/{pathway['total_days'] - 1}"
        if pathway["current_day"] == 0:
            day_label = "Gün 0 (Başlangıç)"
        completion_pct = pathway.get("completion_pct", 0)
        lines.append(f"   İlerleme: {day_label} (%{completion_pct} tamamlandı)")

        task_parts = []
        for task in pathway.get("today_tasks", []):
            mark = "✅" if task["completed"] else "❌"
            task_parts.append(f"{mark} {task['title']}")

        if task_parts:
            completed = pathway.get("today_completed", 0)
            total = pathway.get("today_total", 0)
            lines.append(f"   Bugün: {', '.join(task_parts)} ({completed}/{total})")

    return "\n".join(lines)


def _format_elapsed(days: int) -> str:
    if days == 0:
        return "bugün başladı"
    if days == 1:
        return "dün başladı"
    if days < 7:
        return f"{days} gün önce başladı"
    if days < 30:
        weeks = days // 7
        return f"{weeks} hafta önce başladı"
    months = days // 30
    return f"{months} ay önce başladı"
