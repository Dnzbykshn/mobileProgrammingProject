from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pathway_definition import (
    PathwayDefinition,
    PathwayDefinitionDay,
    PathwayDefinitionTask,
)


def _to_uuid(value):
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


async def list_active_definitions(db: AsyncSession) -> list[PathwayDefinition]:
    result = await db.execute(
        select(PathwayDefinition)
        .where(PathwayDefinition.is_active.is_(True))
        .order_by(PathwayDefinition.created_at.desc())
    )
    return list(result.scalars().all())


async def get_definition_by_id(db: AsyncSession, definition_id) -> Optional[PathwayDefinition]:
    result = await db.execute(
        select(PathwayDefinition).where(PathwayDefinition.id == _to_uuid(definition_id))
    )
    return result.scalar_one_or_none()


async def get_definition_by_slug(db: AsyncSession, slug: str) -> Optional[PathwayDefinition]:
    result = await db.execute(select(PathwayDefinition).where(PathwayDefinition.slug == slug))
    return result.scalar_one_or_none()


async def get_definition_days(db: AsyncSession, definition_id) -> list[PathwayDefinitionDay]:
    result = await db.execute(
        select(PathwayDefinitionDay)
        .where(PathwayDefinitionDay.definition_id == _to_uuid(definition_id))
        .order_by(PathwayDefinitionDay.day_number, PathwayDefinitionDay.order_index)
    )
    return list(result.scalars().all())


async def get_day_tasks(db: AsyncSession, day_ids: list[uuid.UUID]) -> list[PathwayDefinitionTask]:
    if not day_ids:
        return []
    result = await db.execute(
        select(PathwayDefinitionTask)
        .where(PathwayDefinitionTask.definition_day_id.in_(day_ids))
        .order_by(PathwayDefinitionTask.definition_day_id, PathwayDefinitionTask.order_index)
    )
    return list(result.scalars().all())


async def get_definition_with_days_and_tasks(
    db: AsyncSession,
    definition_id,
) -> Optional[tuple[PathwayDefinition, list[tuple[PathwayDefinitionDay, list[PathwayDefinitionTask]]]]]:
    definition = await get_definition_by_id(db, definition_id)
    if not definition:
        return None

    days = await get_definition_days(db, definition.id)
    tasks = await get_day_tasks(db, [day.id for day in days])

    tasks_by_day: dict[uuid.UUID, list[PathwayDefinitionTask]] = {day.id: [] for day in days}
    for task in tasks:
        tasks_by_day.setdefault(task.definition_day_id, []).append(task)

    structured = [(day, tasks_by_day.get(day.id, [])) for day in days]
    return definition, structured
