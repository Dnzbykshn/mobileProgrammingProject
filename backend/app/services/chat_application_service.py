from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import invalidate_context
from app.orchestration import ConversationOrchestrator
from app.repositories.conversation_repository import (
    get_or_create_conversation,
    list_messages,
    save_message,
)
from app.schemas.chat import ChatResponse
from app.services.chat_context_service import ChatContextService


class ChatApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.context_service = ChatContextService(db)
        self.orchestrator = ConversationOrchestrator(db)

    async def handle_message(self, *, message: str, conversation_id: str | None, user_id: str | None) -> dict:
        conversation = await get_or_create_conversation(self.db, conversation_id, user_id)
        await save_message(self.db, conversation.id, "user", message)

        history = await list_messages(self.db, conversation.id)
        user_context = await self.context_service.build_user_context(user_id, message)

        state = {
            "conversation_id": str(conversation.id),
            "user_id": user_id,
            "user_message": message,
            "history": history,
            "current_phase": conversation.phase or "IDLE",
            "user_context": user_context,
        }

        try:
            result = await self.orchestrator.process_turn(state)
        except Exception:
            result = {
                "intent": "CHAT",
                "response_text": "Şu anda kısa süreli bir bağlantı sorunu yaşıyorum. Biraz sonra tekrar deneyelim.",
                "new_phase": conversation.phase or "IDLE",
                "readiness_score": 0,
                "crisis_level": None,
                "emergency_contacts": [],
                "proposal_summary": None,
                "pathway_action": None,
                "pathway_id": None,
            }

        await save_message(
            self.db,
            conversation.id,
            "assistant",
            result["response_text"],
            metadata={"intent": result["intent"], "phase": result["new_phase"]},
        )

        conversation.phase = result["new_phase"]
        if result.get("gathered_insight"):
            context = conversation.gathering_context or {}
            insights = context.get("insights", [])
            insights.append(result["gathered_insight"])
            context["insights"] = insights
            conversation.gathering_context = context

        pathway_id = result.get("pathway_id")
        if pathway_id:
            conversation.pathway_id = UUID(pathway_id)

        await self.db.commit()
        if user_id:
            await invalidate_context(user_id)

        response = ChatResponse(
            intent=result["intent"],
            response_text=result["response_text"],
            conversation_id=str(conversation.id),
            phase=result["new_phase"],
            gathering_progress=result.get("readiness_score"),
            crisis_level=result.get("crisis_level"),
            emergency_contacts=result.get("emergency_contacts"),
            pathway_id=pathway_id,
            pathway_action=result.get("pathway_action"),
            proposal_summary=result.get("proposal_summary"),
        )
        return {
            "response": response,
            "conversation_id": str(conversation.id),
            "user_id": user_id,
            "new_phase": result["new_phase"],
            "user_message": message,
            "gathered_insight": result.get("gathered_insight"),
        }
