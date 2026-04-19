"""Canonical pathway endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_current_user
from app.schemas.pathway import (
    PathwayCreateRequest,
    PathwayDefinitionResponse,
    PathwayDefinitionStartRequest,
    PathwayDefinitionSummary,
    PathwayResponse,
    PathwaySummary,
)
from app.services.pathway_application_service import PathwayApplicationService
from app.services.pathway_definition_service import PathwayDefinitionService

router = APIRouter()


@router.post("/create", response_model=PathwayResponse, status_code=status.HTTP_201_CREATED)
async def create_pathway(
    request: PathwayCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    service = PathwayApplicationService(db)
    return await service.create_pathway(current_user=current_user, request=request)


@router.post("/{pathway_id}/days/0/skip")
async def skip_day0(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    service = PathwayApplicationService(db)
    return await service.skip_day0(pathway_id=pathway_id, current_user=current_user)


@router.get("/active", response_model=List[PathwaySummary])
async def get_active_pathways(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    service = PathwayApplicationService(db)
    return await service.get_active_pathways(current_user=current_user)


@router.get("/definitions", response_model=List[PathwayDefinitionSummary])
async def list_pathway_definitions(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    service = PathwayDefinitionService(db)
    return await service.list_active_definitions()


@router.get("/definitions/{definition_id}", response_model=PathwayDefinitionResponse)
async def get_pathway_definition(
    definition_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    service = PathwayDefinitionService(db)
    return await service.get_definition(definition_id)


@router.post("/definitions/{definition_id}/start", response_model=PathwayResponse, status_code=status.HTTP_201_CREATED)
async def start_pathway_from_definition(
    definition_id: str,
    body: PathwayDefinitionStartRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    definition_service = PathwayDefinitionService(db)
    pathway = await definition_service.start_pathway_from_definition(
        definition_id=definition_id,
        user_id=current_user.id,
        conversation_id=body.conversation_id,
        topic_summary=body.topic_summary or "",
        topic_keywords=body.topic_keywords,
    )

    app_service = PathwayApplicationService(db)
    return await app_service.get_pathway(pathway_id=str(pathway.id), current_user=current_user)


@router.get("/{pathway_id}", response_model=PathwayResponse)
async def get_pathway(
    pathway_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    service = PathwayApplicationService(db)
    return await service.get_pathway(pathway_id=pathway_id, current_user=current_user)


@router.put("/{pathway_id}/tasks/{task_id}/complete")
async def toggle_task(
    pathway_id: str,
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    service = PathwayApplicationService(db)
    return await service.toggle_task(
        pathway_id=pathway_id,
        task_id=task_id,
        current_user=current_user,
    )


@router.post("/{pathway_id}/days/{day_number}/complete")
async def complete_day(
    pathway_id: str,
    day_number: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_current_user),
):
    service = PathwayApplicationService(db)
    return await service.complete_day(
        pathway_id=pathway_id,
        day_number=day_number,
        current_user=current_user,
    )
