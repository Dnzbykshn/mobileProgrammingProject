from __future__ import annotations

from typing import Any

import httpx

from app.core.config import settings
from app.core.exceptions import AppException, NotFoundError


class ResourceServiceError(AppException):
    def __init__(self, detail: str = "Resource service temporarily unavailable", status_code: int = 502):
        super().__init__(detail=detail, status_code=status_code)


class ResourceServiceClient:
    """Thin HTTP client for the external resource service.

    App service owns user flows. Resource service owns content retrieval,
    graph context, and source metadata. This client is the only integration
    boundary between them.
    """

    _client: httpx.AsyncClient | None = None

    def __init__(self) -> None:
        self.base_url = settings.RESOURCE_SERVICE_BASE_URL.rstrip("/")
        self.timeout = httpx.Timeout(settings.RESOURCE_SERVICE_TIMEOUT_SECONDS)
        self.service_token = settings.RESOURCE_SERVICE_TOKEN

    async def list_sources(self) -> dict[str, Any]:
        return await self._request_json("GET", "/resources/sources")

    async def search_content(
        self,
        *,
        query: str,
        limit: int,
        source_types: list[str],
    ) -> dict[str, Any]:
        return await self._request_json(
            "POST",
            "/resources/search",
            json={
                "query": query,
                "limit": limit,
                "source_types": source_types,
            },
        )

    async def get_content_item(self, content_id: int) -> dict[str, Any]:
        return await self._request_json("GET", f"/resources/items/{content_id}")

    async def get_graph_context(
        self,
        *,
        text: str,
        keywords: list[str],
        top_k: int,
    ) -> dict[str, Any]:
        return await self._request_json(
            "POST",
            "/resources/contexts/graph",
            json={
                "text": text,
                "keywords": keywords,
                "top_k": top_k,
            },
        )

    async def _request_json(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not settings.RESOURCE_SERVICE_ENABLED:
            raise ResourceServiceError(
                detail="Resource service integration is disabled",
                status_code=503,
            )
        if not self.base_url:
            raise ResourceServiceError(
                detail="Resource service base URL is not configured",
                status_code=503,
            )
        if not self.service_token:
            raise ResourceServiceError(
                detail="Resource service token is not configured",
                status_code=503,
            )

        headers = {"X-Service-Token": self.service_token}
        url = f"{self.base_url}{path}"

        try:
            client = self._get_client(timeout=self.timeout)
            response = await client.request(method, url, json=json, headers=headers)
        except httpx.HTTPError as exc:
            raise ResourceServiceError(
                detail="Resource service temporarily unavailable",
                status_code=502,
            ) from exc

        payload = self._parse_payload(response)

        if response.status_code == 404:
            raise NotFoundError("Content item")

        if response.status_code >= 400:
            raise ResourceServiceError(
                detail="Resource service temporarily unavailable",
                status_code=502,
            )

        return payload

    @classmethod
    def _get_client(cls, *, timeout: httpx.Timeout) -> httpx.AsyncClient:
        if cls._client is None:
            cls._client = httpx.AsyncClient(timeout=timeout)
        return cls._client

    @classmethod
    async def aclose(cls) -> None:
        if cls._client is None:
            return
        await cls._client.aclose()
        cls._client = None

    @staticmethod
    def _parse_payload(response: httpx.Response) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError:
            payload = {"detail": response.text or "Invalid JSON response"}

        if isinstance(payload, dict):
            return payload
        return {"data": payload}
