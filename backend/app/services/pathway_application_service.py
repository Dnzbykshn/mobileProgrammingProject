"""Application service for pathway endpoints.

Keeps endpoint modules thin and centralizes response formatting.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import pathway_repository
from app.schemas.pathway import (
    PathwayDayGroup,
    PathwayResponse,
    PathwaySummary,
    PathwayTaskResponse,
)
from app.domain.pathways.service import PathwayService


class PathwayApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.pathway_service = PathwayService(db)

    @staticmethod
    def parse_pathway_id_or_400(pathway_id: str) -> UUID:
        try:
            return UUID(pathway_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid pathway ID format") from exc

    async def get_authorized_pathway_or_404(self, pathway_id: str, current_user):
        pathway_uuid = self.parse_pathway_id_or_400(pathway_id)
        pathway = await pathway_repository.get_pathway_by_id_for_user(
            self.db,
            pathway_uuid,
            current_user.id,
        )
        if not pathway:
            raise HTTPException(status_code=404, detail="Pathway not found")
        return pathway

    async def create_pathway(self, *, current_user, request) -> PathwayResponse:
        pathway = await self.pathway_service.create_pathway(
            user_id=current_user.id if current_user else None,
            pathway_type=request.pathway_type,
            source="manual",
            user_context=request.user_input or "",
        )
        result = await self.pathway_service.get_pathway_with_tasks(pathway.id)
        if not result:
            raise HTTPException(status_code=500, detail="Pathway creation failed")
        stored_pathway, days_map = result
        return self.format_pathway_response(stored_pathway, days_map)

    async def get_pathway(self, *, pathway_id: str, current_user) -> PathwayResponse:
        authorized = await self.get_authorized_pathway_or_404(pathway_id, current_user)
        result = await self.pathway_service.get_pathway_with_tasks(authorized.id)
        if not result:
            raise HTTPException(status_code=404, detail="Pathway not found")
        pathway, days_map = result
        return self.format_pathway_response(pathway, days_map)

    async def get_active_pathways(self, *, current_user) -> list[PathwaySummary]:
        pathways = await pathway_repository.get_active_pathways_with_progress(self.db, current_user.id)
        return [
            PathwaySummary(
                pathway_id=str(item["pathway_id"]),
                title=item["title"],
                pathway_type=item["pathway_type"],
                topic_summary=item.get("topic_summary"),
                current_day=item["current_day"],
                total_days=item["total_days"],
                status="active",
                today_completed=item["today_completed"],
                today_total=item["today_total"],
                started_at=item.get("started_at"),
            )
            for item in pathways
        ]

    async def skip_day0(self, *, pathway_id: str, current_user) -> dict:
        authorized = await self.get_authorized_pathway_or_404(pathway_id, current_user)
        if authorized.current_day != 0:
            raise HTTPException(status_code=409, detail="Day 0 can only be skipped at the start")

        pathway = await pathway_repository.skip_pathway_day0(self.db, authorized.id)
        if not pathway:
            raise HTTPException(status_code=404, detail="Pathway not found")
        return {
            "pathway_id": str(pathway.id),
            "current_day": pathway.current_day,
            "message": "Başlangıç günü atlandı, 1. güne geçildi.",
        }

    async def toggle_task(self, *, pathway_id: str, task_id: str, current_user) -> dict:
        authorized = await self.get_authorized_pathway_or_404(pathway_id, current_user)

        task_ref = await pathway_repository.get_pathway_task_by_id(self.db, authorized.id, task_id)
        if not task_ref:
            raise HTTPException(status_code=404, detail="Task not found")
        if task_ref.day_number > authorized.current_day:
            raise HTTPException(status_code=409, detail="Future day tasks cannot be updated yet")

        task = await self.pathway_service.complete_task(task_id, pathway_id=authorized.id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {
            "task_id": str(task.id),
            "is_completed": task.is_completed,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    async def complete_day(self, *, pathway_id: str, day_number: int, current_user) -> dict:
        authorized = await self.get_authorized_pathway_or_404(pathway_id, current_user)

        if day_number != authorized.current_day:
            raise HTTPException(
                status_code=409,
                detail=f"Only current day can be completed. Current day is {authorized.current_day}.",
            )

        tasks = await pathway_repository.get_pathway_tasks(self.db, authorized.id)
        current_day_tasks = [task for task in tasks if task.day_number == day_number]
        if not current_day_tasks:
            raise HTTPException(status_code=409, detail="No tasks found for this day")
        if not all(task.is_completed for task in current_day_tasks):
            raise HTTPException(status_code=409, detail="Complete all tasks before finishing the day")

        pathway = await self.pathway_service.complete_day(authorized.id, day_number)
        if not pathway:
            raise HTTPException(status_code=404, detail="Pathway not found")
        return {
            "pathway_id": str(pathway.id),
            "current_day": pathway.current_day,
            "status": pathway.status,
            "message": (
                "Tebrikler! Bir sonraki güne geçtiniz."
                if pathway.status == "active"
                else "Yol tamamlandı! 🎉"
            ),
        }

    @staticmethod
    def format_pathway_response(pathway, days_map: dict) -> PathwayResponse:
        day_groups = []
        for day_num in sorted(days_map.keys()):
            tasks = days_map[day_num]
            task_responses = [
                PathwayTaskResponse(
                    id=str(task.id),
                    day_number=task.day_number,
                    task_type=task.task_type,
                    title=task.title,
                    description=task.description,
                    duration_minutes=task.duration_minutes,
                    order_index=task.order_index,
                    is_completed=task.is_completed,
                    completed_at=task.completed_at,
                    task_metadata=task.task_metadata,
                )
                for task in tasks
            ]
            day_groups.append(
                PathwayDayGroup(
                    day_number=day_num,
                    tasks=task_responses,
                    is_complete=all(task.is_completed for task in tasks),
                    is_day0=day_num == 0,
                    is_skippable=day_num == 0,
                )
            )

        return PathwayResponse(
            id=str(pathway.id),
            title=pathway.title or "",
            pathway_type=pathway.pathway_type or "",
            total_days=pathway.total_days,
            current_day=pathway.current_day,
            status=pathway.status,
            started_at=pathway.started_at,
            days=day_groups,
            topic_summary=pathway.topic_summary,
            day0_skipped=pathway.day0_skipped,
        )
