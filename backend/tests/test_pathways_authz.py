import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.pathways import router as pathways_router
from app.core.dependencies import get_db, require_current_user


class PathwaysAuthorizationTests(unittest.TestCase):
    def _build_app(self, current_user):
        app = FastAPI()
        app.include_router(pathways_router, prefix="/pathways")

        async def override_get_db():
            yield object()

        app.dependency_overrides[get_db] = override_get_db
        if current_user is not None:
            def override_require_current_user():
                return current_user

            app.dependency_overrides[require_current_user] = override_require_current_user
        return app

    def test_pathways_requires_authentication(self):
        app = self._build_app(None)

        response = TestClient(app).get(f"/pathways/{uuid.uuid4()}")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("detail"), "Authentication required")

    def test_pathways_scopes_to_current_user(self):
        user_id = uuid.uuid4()
        app = self._build_app(SimpleNamespace(id=user_id))
        pathway_id = str(uuid.uuid4())

        with patch(
            "app.services.pathway_application_service.pathway_repository.get_pathway_by_id_for_user",
            new=AsyncMock(return_value=None),
        ) as get_pathway_by_id_for_user:
            response = TestClient(app).get(f"/pathways/{pathway_id}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("detail"), "Pathway not found")
        get_pathway_by_id_for_user.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
