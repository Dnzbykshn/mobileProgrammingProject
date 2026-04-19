"""
Small in-process TTL cache helpers.

This cache is intentionally best-effort. It reduces repeated work inside a
single backend process, but correctness must always come from PostgreSQL.
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import time
from typing import Any, Optional


AI_CACHE_TTL = 86400
CTX_TTL = 300
MAX_CACHE_ITEMS = 1024

_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = asyncio.Lock()


def _hash(text: str) -> str:
    return hashlib.sha256(text.lower().strip().encode("utf-8")).hexdigest()[:16]


async def _get(key: str) -> Optional[Any]:
    async with _cache_lock:
        item = _cache.get(key)
        if item is None:
            return None

        expires_at, value = item
        if expires_at <= time.monotonic():
            _cache.pop(key, None)
            return None

        return copy.deepcopy(value)


async def _set(key: str, value: Any, ttl: int) -> None:
    async with _cache_lock:
        if len(_cache) >= MAX_CACHE_ITEMS:
            now = time.monotonic()
            expired_keys = [
                cache_key
                for cache_key, (expires_at, _) in _cache.items()
                if expires_at <= now
            ]
            for expired_key in expired_keys:
                _cache.pop(expired_key, None)

            if len(_cache) >= MAX_CACHE_ITEMS:
                oldest_key = min(_cache, key=lambda cache_key: _cache[cache_key][0])
                _cache.pop(oldest_key, None)

        _cache[key] = (time.monotonic() + ttl, copy.deepcopy(value))


async def _delete(key: str) -> None:
    async with _cache_lock:
        _cache.pop(key, None)


async def get_cached_guardrail(message: str) -> Optional[dict]:
    return await _get(f"guard:{_hash(message)}")


async def set_cached_guardrail(message: str, result: Optional[dict]) -> None:
    await _set(f"guard:{_hash(message)}", result if result else {"safe": True}, ttl=AI_CACHE_TTL)


async def get_cached_context(user_id: str) -> Optional[dict]:
    return await _get(f"ctx:{user_id}")


async def set_cached_context(user_id: str, context: dict) -> None:
    serializable = {
        "profile_str": context.get("profile_str", ""),
        "pathways_str": context.get("pathways_str", ""),
        "active_pathways": context.get("active_pathways", []),
        "cross_history": context.get("cross_history", []),
        "memory_str": context.get("memory_str", ""),
        "spiritual_prefs": context.get("spiritual_prefs", ""),
        "language_style": context.get("language_style", {}),
        "language_style_str": context.get("language_style_str", "Standart"),
        "conversational_tone": context.get("conversational_tone", "polite_formal"),
    }
    await _set(f"ctx:{user_id}", serializable, ttl=CTX_TTL)


async def invalidate_context(user_id: str) -> None:
    await _delete(f"ctx:{user_id}")
