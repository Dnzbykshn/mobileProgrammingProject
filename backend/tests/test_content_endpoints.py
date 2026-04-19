import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.content import router as content_router
from app.core.dependencies import get_db


class ContentEndpointTests(unittest.TestCase):
    def _build_app(self):
        app = FastAPI()
        app.include_router(content_router, prefix="/content")

        async def override_get_db():
            yield object()

        app.dependency_overrides[get_db] = override_get_db
        return app

    def test_list_sources_returns_backend_values(self):
        app = self._build_app()

        with patch(
            "app.api.v1.endpoints.content.ContentService.list_source_types",
            new=AsyncMock(return_value=["book", "quran"]),
        ):
            response = TestClient(app).get("/content/sources")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sources"], ["book", "quran"])

    def test_search_returns_serialized_results(self):
        app = self._build_app()
        fake_result = SimpleNamespace(
            model_dump=lambda: {
                "id": 1,
                "source_type": "quran",
                "content_text": "Sabredenlerle beraberim",
                "explanation": "Teselli mesajı",
                "metadata": {"surah_name": "Bakara"},
                "score_hint": "simple",
            }
        )

        with patch(
            "app.api.v1.endpoints.content.ContentService.search",
            new=AsyncMock(return_value=[fake_result]),
        ):
            response = TestClient(app).post(
                "/content/search",
                json={"query": "sabır", "limit": 1, "source_types": ["quran"]},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["source_type"], "quran")

    def test_get_content_item_returns_404_when_missing(self):
        app = self._build_app()

        with patch(
            "app.api.v1.endpoints.content.ContentService.get_content_item",
            new=AsyncMock(side_effect=LookupError("Content item not found")),
        ):
            response = TestClient(app).get("/content/items/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["detail"], "Content item not found")


if __name__ == "__main__":
    unittest.main()
