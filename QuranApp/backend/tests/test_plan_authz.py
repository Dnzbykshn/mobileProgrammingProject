import unittest
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.plan import router as plan_router
from app.core.dependencies import get_current_user, get_db


class PlanAuthorizationTests(unittest.TestCase):
    def _build_app(self, current_user):
        app = FastAPI()
        app.include_router(plan_router, prefix="/plans")

        async def override_get_db():
            yield object()

        def override_get_current_user():
            return current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        return app

    def test_get_plan_returns_404_for_other_users_plan(self):
        user_id = uuid.uuid4()
        app = self._build_app(SimpleNamespace(id=user_id))
        plan_id = str(uuid.uuid4())

        with (
            patch(
                "app.api.v1.endpoints.plan.plan_repository.get_plan_by_id_for_user",
                new=AsyncMock(return_value=None),
            ) as get_plan_by_id_for_user,
            patch(
                "app.api.v1.endpoints.plan.plan_repository.get_anonymous_plan_by_id",
                new=AsyncMock(return_value=None),
            ) as get_anonymous_plan_by_id,
        ):
            response = TestClient(app).get(f"/plans/{plan_id}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("detail"), "Plan not found")
        get_plan_by_id_for_user.assert_awaited_once()
        get_anonymous_plan_by_id.assert_not_awaited()

        called_db, called_plan_id, called_user_id = get_plan_by_id_for_user.await_args.args
        self.assertIsNotNone(called_db)
        self.assertEqual(str(called_plan_id), plan_id)
        self.assertEqual(str(called_user_id), str(user_id))

    def test_toggle_task_returns_404_for_other_users_plan(self):
        user_id = uuid.uuid4()
        app = self._build_app(SimpleNamespace(id=user_id))
        plan_id = str(uuid.uuid4())
        task_id = str(uuid.uuid4())

        with (
            patch(
                "app.api.v1.endpoints.plan.plan_repository.get_plan_by_id_for_user",
                new=AsyncMock(return_value=None),
            ) as get_plan_by_id_for_user,
            patch(
                "app.api.v1.endpoints.plan.plan_repository.get_anonymous_plan_by_id",
                new=AsyncMock(return_value=None),
            ) as get_anonymous_plan_by_id,
        ):
            response = TestClient(app).put(f"/plans/{plan_id}/tasks/{task_id}/complete")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("detail"), "Plan not found")
        get_plan_by_id_for_user.assert_awaited_once()
        get_anonymous_plan_by_id.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
