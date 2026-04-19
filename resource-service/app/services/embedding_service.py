from __future__ import annotations

import asyncio

from google import genai

from app.core.config import settings

_client: genai.Client | None = None


def get_gemini_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def get_embedding_sync(text: str, *, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    client = get_gemini_client()
    result = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text,
        config={
            "output_dimensionality": settings.EMBEDDING_DIMENSION,
            "task_type": task_type,
        },
    )
    return result.embeddings[0].values


async def get_embedding(text: str, *, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    return await asyncio.to_thread(get_embedding_sync, text, task_type=task_type)
