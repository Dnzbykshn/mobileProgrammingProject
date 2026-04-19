from __future__ import annotations

import uuid

from app.core.cache import invalidate_context
from app.db.database import AsyncSessionLocal
from app.services.chat_context_service import ChatContextService
from app.services.memory_extraction_service import extract_memories_from_conversation


class ChatPostprocessService:
    """Runs non-critical post-response work outside the request path."""

    @staticmethod
    async def run(
        *,
        conversation_id: str,
        user_id: str | None,
        new_phase: str,
        user_message: str,
        gathered_insight: str | None,
    ) -> None:
        if not user_id:
            return

        async with AsyncSessionLocal() as session:
            context_service = ChatContextService(session)

            if new_phase == "GENERATED":
                try:
                    created_ids = await extract_memories_from_conversation(session, uuid.UUID(conversation_id))
                    if created_ids:
                        await invalidate_context(user_id)
                except Exception:
                    pass

            try:
                await context_service.update_profile_after_turn(
                    user_id=user_id,
                    user_message=user_message,
                    gathered_insight=gathered_insight,
                )
                await invalidate_context(user_id)
            except Exception:
                pass
