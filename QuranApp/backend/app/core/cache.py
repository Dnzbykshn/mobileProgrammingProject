"""
Redis caching utilities for the Spiritual Therapy API.
Provides typed helpers for chat history, AI responses, and user context.
"""
import hashlib
import json
from typing import Optional, Any, List

import redis.asyncio as aioredis

from app.core.config import settings


# ─────────────────────────────
# Key helpers
# ─────────────────────────────

def _hash(text: str) -> str:
    """SHA-256 hash for cache keys."""
    return hashlib.sha256(text.lower().strip().encode("utf-8")).hexdigest()[:16]


# ─────────────────────────────
# Generic get / set
# ─────────────────────────────

async def cache_get(redis_client: Optional[aioredis.Redis], key: str) -> Optional[dict]:
    """Read JSON from cache. Returns None on miss or error."""
    if not redis_client:
        return None
    try:
        cached = await redis_client.get(key)
        if cached:
            return json.loads(cached)
    except Exception as e:
        print(f"⚠️ Redis read error: {e}")
    return None


async def cache_set(
    redis_client: Optional[aioredis.Redis],
    key: str,
    value: Any,
    ttl: int = settings.REDIS_CACHE_TTL,
) -> None:
    """Write JSON to cache with TTL. Silently ignores errors."""
    if not redis_client:
        return
    try:
        if hasattr(value, "model_dump_json"):
            data = value.model_dump_json()
        else:
            data = json.dumps(value, ensure_ascii=False)
        await redis_client.setex(key, ttl, data)
    except Exception as e:
        print(f"⚠️ Redis write error: {e}")


# ─────────────────────────────
# 1. Chat History Cache
# ─────────────────────────────

CHAT_TTL = 3600  # 1 hour


async def get_cached_history(
    redis_client: Optional[aioredis.Redis], conv_id: str
) -> Optional[List[dict]]:
    """Get cached conversation history."""
    return await cache_get(redis_client, f"chat:{conv_id}")


async def set_cached_history(
    redis_client: Optional[aioredis.Redis], conv_id: str, history: List[dict]
) -> None:
    """Cache conversation history (last 20 messages)."""
    trimmed = history[-20:]  # Keep only last 20
    await cache_set(redis_client, f"chat:{conv_id}", trimmed, ttl=CHAT_TTL)


async def invalidate_history(
    redis_client: Optional[aioredis.Redis], conv_id: str
) -> None:
    """Invalidate chat cache (called when new message saved)."""
    if redis_client:
        try:
            await redis_client.delete(f"chat:{conv_id}")
        except Exception:
            pass


# ─────────────────────────────
# 2. AI Response Cache
# ─────────────────────────────

AI_CACHE_TTL = 86400  # 24 hours


async def get_cached_guardrail(
    redis_client: Optional[aioredis.Redis], message: str
) -> Optional[dict]:
    """Check if a guardrail result is cached for this message."""
    return await cache_get(redis_client, f"guard:{_hash(message)}")


async def set_cached_guardrail(
    redis_client: Optional[aioredis.Redis], message: str, result: Optional[dict]
) -> None:
    """Cache guardrail check result."""
    value = result if result else {"safe": True}
    await cache_set(redis_client, f"guard:{_hash(message)}", value, ttl=AI_CACHE_TTL)


# ─────────────────────────────
# 3. User Context Cache
# ─────────────────────────────

CTX_TTL = 300  # 5 minutes


async def get_cached_context(
    redis_client: Optional[aioredis.Redis], user_id: str
) -> Optional[dict]:
    """Get cached user context (profile + plans)."""
    return await cache_get(redis_client, f"ctx:{user_id}")


async def set_cached_context(
    redis_client: Optional[aioredis.Redis], user_id: str, context: dict
) -> None:
    """Cache user context. Strips non-serializable objects (profile ORM model)."""
    serializable = {
        "profile_str": context.get("profile_str", ""),
        "plans_str": context.get("plans_str", ""),
        "active_plans": context.get("active_plans", []),
        "cross_history": context.get("cross_history", []),
    }
    await cache_set(redis_client, f"ctx:{user_id}", serializable, ttl=CTX_TTL)


async def invalidate_context(
    redis_client: Optional[aioredis.Redis], user_id: str
) -> None:
    """Invalidate user context cache (called when journeys change)."""
    if redis_client:
        try:
            await redis_client.delete(f"ctx:{user_id}")
        except Exception:
            pass
