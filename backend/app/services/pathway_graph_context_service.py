from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.integrations.resource_service import ResourceServiceClient, ResourceServiceError


class PathwayGraphContextService:
    """App-side adapter for pathway graph context.

    The app service does not know anything about Neo4j, keyword vectors, or
    taxonomy storage. It asks the resource service for graph context and keeps
    a best-effort fallback so pathway generation can continue even if the
    content subsystem is unavailable.
    """

    def __init__(self) -> None:
        self.client = ResourceServiceClient()

    async def get_context(
        self,
        *,
        user_text: str,
        keywords: list[str] | None = None,
        top_k: int = 8,
    ) -> dict[str, Any]:
        if not settings.RESOURCE_SERVICE_ENABLED:
            return self._empty()

        if not user_text.strip() and not (keywords or []):
            return self._empty()

        try:
            return await self.client.get_graph_context(
                text=user_text[:1500],
                keywords=keywords or [],
                top_k=top_k,
            )
        except ResourceServiceError:
            return self._empty()
        except Exception:
            return self._empty()

    @staticmethod
    def _empty() -> dict[str, Any]:
        return {
            "graph_keywords": [],
            "graph_passages": [],
            "graph_sub_categories": [],
            "graph_root_categories": [],
            "graph_summary": "",
            "suggested_pathway_type": None,
        }
