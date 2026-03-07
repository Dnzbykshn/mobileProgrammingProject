"""
Centralized AI Service — Single point of access for Gemini API.
All services should use this instead of creating their own genai.Client.
"""
import asyncio
import time
from google import genai

from app.core.config import settings

# Singleton client — created once, shared across services
_client = None


def get_gemini_client() -> genai.Client:
    """Get or create the singleton Gemini client."""
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
    return _client


def _reset_client():
    """Reset singleton client (called on connection errors)."""
    global _client
    _client = None
    print("🔄 Gemini client reset due to connection error")


def generate_content_sync(prompt: str, response_schema=None) -> any:
    """Sync Gemini content generation with retry on connection errors."""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            client = get_gemini_client()
            config = {}
            if response_schema:
                config["response_mime_type"] = "application/json"
                config["response_schema"] = response_schema
            return client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=prompt,
                config=config if config else None,
            )
        except Exception as e:
            error_msg = str(e).lower()
            is_connection_error = any(
                keyword in error_msg
                for keyword in ["connect", "nodename", "dns", "timeout", "errno"]
            )
            if is_connection_error and attempt < max_retries - 1:
                print(f"⚠️ Gemini connection failed (attempt {attempt + 1}), resetting client...")
                _reset_client()
                time.sleep(0.5)  # Brief pause before retry
                continue
            raise  # Re-raise if not connection error or last attempt


async def generate_content(prompt: str, response_schema=None) -> any:
    """Async wrapper for Gemini content generation."""
    return await asyncio.to_thread(generate_content_sync, prompt, response_schema)


def get_embedding_sync(text: str) -> list:
    """Sync embedding generation."""
    client = get_gemini_client()
    result = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=text,
        config={"output_dimensionality": settings.EMBEDDING_DIMENSION},
    )
    return result.embeddings[0].values


async def get_embedding(text: str) -> list:
    """Async embedding generation."""
    return await asyncio.to_thread(get_embedding_sync, text)

