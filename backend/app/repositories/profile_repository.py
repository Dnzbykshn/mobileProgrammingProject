"""
Profile repository — async database operations for user profiles.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid

from app.models.user_profile import UserProfile


async def get_or_create_profile(
    db: AsyncSession, user_id
) -> UserProfile:
    """Get existing profile or create a blank one."""
    uid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == uid)
    )
    profile = result.scalar_one_or_none()
    if profile:
        return profile

    profile = UserProfile(user_id=uid)
    db.add(profile)
    await db.flush()
    return profile


async def update_profile(
    db: AsyncSession,
    user_id,
    *,
    display_name: Optional[str] = None,
    new_topics: Optional[list] = None,
    personality_notes: Optional[str] = None,
    last_mood: Optional[str] = None,
    increment_interactions: int = 0,
) -> UserProfile:
    """Update profile fields. Merges new_topics into existing list."""
    profile = await get_or_create_profile(db, user_id)

    if display_name:
        profile.display_name = display_name

    if new_topics:
        existing = profile.known_topics or []
        merged = list(set(existing + new_topics))
        profile.known_topics = merged

    if personality_notes:
        old = profile.personality_notes or ""
        # Append new notes (keep last 500 chars to avoid bloat)
        combined = f"{old}\n{personality_notes}".strip()
        profile.personality_notes = combined[-500:]

    if last_mood:
        profile.last_mood = last_mood

    if increment_interactions > 0:
        profile.interaction_count = (profile.interaction_count or 0) + increment_interactions
        # Auto-evolve tone: formal → samimi after 10 interactions
        if profile.interaction_count >= 10 and profile.preferred_tone == "formal":
            profile.preferred_tone = "samimi"

    await db.flush()
    return profile


def profile_to_context_str(profile: UserProfile) -> str:
    """Convert profile to a string for AI prompt injection."""
    parts = []

    name = profile.display_name or "Kullanıcı"
    parts.append(f"İsim: {name}")

    if profile.known_topics:
        parts.append(f"Bilinen konular: {', '.join(profile.known_topics)}")

    parts.append(f"Etkileşim sayısı: {profile.interaction_count or 0}")

    tone_desc = "samimi ve sıcak" if profile.preferred_tone == "samimi" else "saygılı ama yakın"
    parts.append(f"İletişim tonu: {tone_desc}")

    if profile.last_mood:
        parts.append(f"Son ruh hali: {profile.last_mood}")

    if profile.personality_notes:
        # Last 200 chars of notes
        notes = profile.personality_notes[-200:]
        parts.append(f"Notlar: {notes}")

    return "\n".join(parts)
