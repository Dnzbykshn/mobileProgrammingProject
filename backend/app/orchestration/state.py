from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict

from pydantic import BaseModel


ConversationPhase = Literal["IDLE", "GATHERING", "PROPOSING", "READY", "GENERATED", "ONGOING"]
NodeRoute = Literal[
    "guardrail",
    "idle",
    "gathering",
    "proposing",
    "ongoing",
    "diagnosis",
    "pathway",
    "finalize",
]


class OrchestratorState(TypedDict, total=False):
    conversation_id: str
    user_id: Optional[str]
    user_message: str
    history: list[dict[str, str]]
    current_phase: ConversationPhase
    user_context: dict[str, Any]
    guardrail_hit: bool
    route: NodeRoute
    intent: str
    response_text: str
    new_phase: ConversationPhase
    readiness_score: int
    gathered_insight: str
    proposal_summary: str
    crisis_level: Optional[str]
    emergency_contacts: list[dict[str, str]]
    should_generate_pathway: bool
    diagnosis: Optional[dict[str, Any]]
    pathway_action: Optional[str]
    pathway_id: Optional[str]


class IntentDecision(BaseModel):
    intent: Literal["CHAT", "SUPPORT"]
    response_text: str


class GatheringDecision(BaseModel):
    response_text: str
    readiness_score: int
    gathered_insight: str
    proposal_summary: str = ""


class OngoingDecision(BaseModel):
    response_type: Literal["pathway_feedback", "new_topic", "general_chat"]
    response_text: str
    should_update_pathway: bool = False
