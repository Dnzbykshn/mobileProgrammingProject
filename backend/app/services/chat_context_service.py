from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cached_context, set_cached_context
from app.models.user_profile import UserProfile
from app.repositories import memory_repository, pathway_repository, profile_repository
from app.repositories.conversation_repository import get_cross_conversation_history
from app.repositories.memory_repository import (
    format_language_style,
    memories_to_context_str,
    spiritual_preferences_to_context_str,
)
from app.repositories.profile_repository import profile_to_context_str
from app.services.ai_service import get_embedding
from app.services.language_style_analyzer import (
    evolve_conversational_tone,
    extract_language_features,
)


class ChatContextService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def build_user_context(
        self,
        user_id: Optional[str],
        current_message: Optional[str] = None,
    ) -> dict:
        if not user_id:
            return {
                "profile_str": "Anonim kullanıcı (giriş yapmamış).",
                "pathways_str": "Aktif yol yok.",
                "active_pathways": [],
                "cross_history": [],
                "memory_str": "",
                "spiritual_prefs": "",
                "language_style": {},
                "language_style_str": "Standart",
                "conversational_tone": "polite_formal",
            }

        cached = await get_cached_context(user_id)
        if cached:
            if current_message:
                cached["memory_str"] = await self._retrieve_memory_context(uuid.UUID(user_id), current_message)
            return cached

        uid = uuid.UUID(user_id)
        profile = await profile_repository.get_or_create_profile(self.db, uid)
        active_pathways = await pathway_repository.get_active_pathways_with_progress(self.db, uid)
        cross_history = await get_cross_conversation_history(self.db, uid, limit=20)
        memory_str = await self._retrieve_memory_context(uid, current_message) if current_message else ""
        spiritual_prefs = spiritual_preferences_to_context_str(profile.spiritual_preferences or {})
        language_style = profile.language_style or {}
        conversational_tone = profile.conversational_tone or "polite_formal"

        context = {
            "profile_str": profile_to_context_str(profile),
            "pathways_str": pathway_repository.active_pathways_to_context_str(active_pathways),
            "active_pathways": active_pathways,
            "cross_history": cross_history,
            "memory_str": memory_str,
            "spiritual_prefs": spiritual_prefs,
            "language_style": language_style,
            "language_style_str": format_language_style(language_style),
            "conversational_tone": conversational_tone,
        }
        await set_cached_context(user_id, context)
        return context

    async def _retrieve_memory_context(self, user_id: uuid.UUID, current_message: str) -> str:
        try:
            embedding = await get_embedding(current_message)
            memories = await memory_repository.retrieve_relevant_memories(
                self.db,
                user_id,
                embedding,
                limit=4,
            )
            return memories_to_context_str(memories)
        except Exception:
            return ""

    async def update_profile_after_turn(
        self,
        *,
        user_id: Optional[str],
        user_message: str,
        gathered_insight: Optional[str],
    ) -> None:
        if not user_id:
            return

        await profile_repository.update_profile(
            self.db,
            user_id,
            last_mood=(gathered_insight or user_message)[:50],
            increment_interactions=1,
        )
        await self.db.commit()

        profile_result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == uuid.UUID(user_id))
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            return

        current_style = profile.language_style or {}
        updated_style = extract_language_features(user_message, current_style)
        updated_style["last_updated"] = datetime.now(timezone.utc).isoformat()

        interaction_count = profile.interaction_count or 0
        relationship_start = profile.relationship_start_date or datetime.now(timezone.utc)
        relationship_days = (datetime.now(timezone.utc) - relationship_start).days
        profile.language_style = updated_style
        profile.conversational_tone = evolve_conversational_tone(interaction_count, relationship_days)
        await self.db.commit()
