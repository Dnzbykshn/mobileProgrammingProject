from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.pathways.models import PathwayBlueprint, PathwayDayDraft, PathwayTaskDraft
from app.domain.pathways.service import PathwayService
from app.repositories import pathway_definition_repository


class PathwayDefinitionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pathway_service = PathwayService(db)

    @staticmethod
    def parse_definition_id_or_400(definition_id: str) -> UUID:
        try:
            return UUID(definition_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid pathway definition ID format") from exc

    async def list_active_definitions(self) -> list[dict]:
        definitions = await pathway_definition_repository.list_active_definitions(self.db)
        return [
            {
                "id": str(item.id),
                "slug": item.slug,
                "title": item.title,
                "pathway_type": item.pathway_type,
                "summary": item.summary,
                "total_days": item.total_days,
            }
            for item in definitions
        ]

    async def get_definition(self, definition_id: str) -> dict:
        definition_uuid = self.parse_definition_id_or_400(definition_id)
        structured = await pathway_definition_repository.get_definition_with_days_and_tasks(
            self.db,
            definition_uuid,
        )
        if not structured:
            raise HTTPException(status_code=404, detail="Pathway definition not found")

        definition, days_with_tasks = structured
        if not definition.is_active:
            raise HTTPException(status_code=404, detail="Pathway definition not found")

        return {
            "id": str(definition.id),
            "slug": definition.slug,
            "title": definition.title,
            "pathway_type": definition.pathway_type,
            "summary": definition.summary,
            "total_days": definition.total_days,
            "days": [
                {
                    "day_number": day.day_number,
                    "title": day.title,
                    "description": day.description,
                    "is_day0": day.is_day0,
                    "is_skippable": day.is_skippable,
                    "tasks": [
                        {
                            "id": str(task.id),
                            "task_type": task.task_type,
                            "title": task.title,
                            "description": task.description,
                            "duration_minutes": task.duration_minutes,
                            "order_index": task.order_index,
                            "task_metadata": task.task_metadata,
                        }
                        for task in tasks
                    ],
                }
                for day, tasks in days_with_tasks
            ],
        }

    async def start_pathway_from_definition(
        self,
        *,
        definition_id: str,
        user_id,
        conversation_id: Optional[str] = None,
        topic_summary: str = "",
        topic_keywords: Optional[list[str]] = None,
    ):
        definition_uuid = self.parse_definition_id_or_400(definition_id)
        structured = await pathway_definition_repository.get_definition_with_days_and_tasks(
            self.db,
            definition_uuid,
        )
        if not structured:
            raise HTTPException(status_code=404, detail="Pathway definition not found")

        definition, days_with_tasks = structured
        if not definition.is_active:
            raise HTTPException(status_code=404, detail="Pathway definition not found")
        if not days_with_tasks:
            raise HTTPException(status_code=409, detail="Pathway definition has no day structure")

        day_drafts = [
            PathwayDayDraft(
                day_number=day.day_number,
                tasks=[
                    PathwayTaskDraft(
                        day_number=day.day_number,
                        task_type=task.task_type,
                        title=task.title,
                        description=task.description or "",
                        duration_minutes=task.duration_minutes or 5,
                        order_index=task.order_index,
                        metadata=task.task_metadata or {},
                    )
                    for task in tasks
                ],
            )
            for day, tasks in days_with_tasks
        ]

        total_days = max(
            definition.total_days or 0,
            max((day.day_number for day, _ in days_with_tasks), default=0) + 1,
        )
        blueprint = PathwayBlueprint(
            title=definition.title,
            pathway_type=definition.pathway_type,
            topic_summary=topic_summary or definition.summary or "",
            topic_keywords=topic_keywords or [],
            source="admin",
            total_days=total_days,
            days=day_drafts,
        )

        try:
            conversation_uuid = UUID(conversation_id) if conversation_id else None
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format") from exc

        return await self.pathway_service.instantiate_blueprint(
            user_id=user_id,
            conversation_id=conversation_uuid,
            blueprint=blueprint,
        )
