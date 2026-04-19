from __future__ import annotations

import uuid
from typing import Any, Optional, TypedDict

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.pathways.service import PathwayService
from app.repositories import pathway_repository
from app.repositories.conversation_repository import conversation_history_to_text
from app.services.pathway_decision_service import PathwayDecisionService

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover
    END = "__end__"
    START = "__start__"
    StateGraph = None


class PathwayGenerationState(TypedDict, total=False):
    user_id: str
    conversation_id: str
    history: list[dict[str, str]]
    diagnosis: dict[str, Any]

    history_text: str
    pathway_type: str
    topic_summary: str
    topic_keywords: list[str]
    active_pathways: list[dict[str, Any]]
    decision: Any

    pathway_action: Optional[str]
    pathway_id: Optional[str]
    response_text: str
    new_phase: str


class PathwayGenerationOrchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._compiled_graph = self._build_graph() if StateGraph else None

    async def generate(self, state: PathwayGenerationState) -> dict[str, Any]:
        if self._compiled_graph is not None:
            result = await self._compiled_graph.ainvoke(state)
        else:
            result = await self._fallback_invoke(state)

        return {
            "pathway_action": result.get("pathway_action"),
            "pathway_id": result.get("pathway_id"),
            "response_text": result.get("response_text"),
            "new_phase": result.get("new_phase", "GENERATED"),
        }

    def _build_graph(self):
        graph = StateGraph(PathwayGenerationState)
        graph.add_node("prepare", self.prepare_node)
        graph.add_node("load_active", self.load_active_pathways_node)
        graph.add_node("decide", self.decide_node)
        graph.add_node("apply", self.apply_node)

        graph.add_edge(START, "prepare")
        graph.add_edge("prepare", "load_active")
        graph.add_edge("load_active", "decide")
        graph.add_edge("decide", "apply")
        graph.add_edge("apply", END)
        return graph.compile()

    async def _fallback_invoke(self, state: PathwayGenerationState) -> PathwayGenerationState:
        prepared = await self.prepare_node(state)
        enriched = {**state, **prepared}

        loaded = await self.load_active_pathways_node(enriched)
        enriched = {**enriched, **loaded}

        decided = await self.decide_node(enriched)
        enriched = {**enriched, **decided}

        applied = await self.apply_node(enriched)
        return {**enriched, **applied}

    async def prepare_node(self, state: PathwayGenerationState) -> dict[str, Any]:
        diagnosis = state["diagnosis"]
        emotion = diagnosis.get("emotional_state", "").lower()
        emotion_map = {
            "kaygı": "anxiety_management",
            "korku": "anxiety_management",
            "stres": "anxiety_management",
            "hüzün": "grief_healing",
            "üzüntü": "grief_healing",
            "yas": "grief_healing",
            "öfke": "anger_control",
        }
        pathway_type = emotion_map.get(emotion, "spiritual_growth")

        topic_summary = (
            f"{diagnosis.get('emotional_state', 'Duygu')}: {diagnosis.get('root_cause', '')[:120]}"
        ).strip()
        topic_keywords = diagnosis.get("search_keywords", [])
        history_text = conversation_history_to_text(state["history"])

        return {
            "history_text": history_text,
            "pathway_type": pathway_type,
            "topic_summary": topic_summary,
            "topic_keywords": topic_keywords,
        }

    async def load_active_pathways_node(self, state: PathwayGenerationState) -> dict[str, Any]:
        active_pathways = await pathway_repository.get_active_pathways_with_progress(
            self.db,
            uuid.UUID(state["user_id"]),
        )
        return {"active_pathways": active_pathways}

    async def decide_node(self, state: PathwayGenerationState) -> dict[str, Any]:
        active_pathways = state.get("active_pathways") or []
        if not active_pathways:
            return {"decision": None}

        decision_service = PathwayDecisionService(self.db)
        decision = await decision_service.decide(
            user_id=state["user_id"],
            diagnosis=state["diagnosis"],
            active_pathways=active_pathways,
        )
        return {"decision": decision}

    async def apply_node(self, state: PathwayGenerationState) -> dict[str, Any]:
        service = PathwayService(self.db)
        decision = state.get("decision")

        if decision and decision.action == "update_pathway" and decision.confidence >= 0.7:
            pathway = await service.update_pathway_remaining_days(
                pathway_id=decision.matching_pathway_id,
                new_user_context=state["history_text"][-500:],
                new_pathway_type=state["pathway_type"],
                topic_summary=state["topic_summary"],
                topic_keywords=state["topic_keywords"],
            )
            pathway_id = str(pathway.id) if pathway else decision.matching_pathway_id
            return {
                "pathway_action": "updated",
                "pathway_id": pathway_id,
                "response_text": "Mevcut yolunu, yeni paylaştığın duruma göre güncelledim. Tamamlanan günlerin yerinde kaldı.",
                "new_phase": "GENERATED",
            }

        pathway = await service.create_pathway(
            user_id=state["user_id"],
            conversation_id=state["conversation_id"],
            pathway_type=state["pathway_type"],
            source="chat",
            user_context=state["history_text"][-500:],
            topic_summary=state["topic_summary"],
            topic_keywords=state["topic_keywords"],
        )
        return {
            "pathway_action": "created",
            "pathway_id": str(pathway.id),
            "response_text": "Senin için sade ve takip edilebilir bir yol hazırladım. Önce başlangıç gününe bak, sonra günlük küçük adımlarla devam et.",
            "new_phase": "GENERATED",
        }
