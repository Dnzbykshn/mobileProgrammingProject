import unittest
import uuid
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.prescriptions import router as prescriptions_router
from app.core.dependencies import get_current_user, get_db


class _FakeScalarResult:
    def scalar_one_or_none(self):
        return None


class _FakeDB:
    def __init__(self):
        self.last_statement = None

    async def execute(self, statement):
        self.last_statement = statement
        return _FakeScalarResult()


class PrescriptionsAuthorizationTests(unittest.TestCase):
    def _build_app(self, db, current_user):
        app = FastAPI()
        app.include_router(prescriptions_router, prefix="/prescriptions")

        async def override_get_db():
            yield db

        def override_get_current_user():
            return current_user

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_current_user] = override_get_current_user
        return app

    def test_list_requires_authentication(self):
        app = self._build_app(_FakeDB(), None)

        response = TestClient(app).get("/prescriptions/")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("detail"), "Authentication required")

    def test_detail_scopes_query_to_current_user_and_returns_404_when_not_owned(self):
        fake_db = _FakeDB()
        current_user = SimpleNamespace(id=uuid.uuid4())
        app = self._build_app(fake_db, current_user)
        prescription_id = str(uuid.uuid4())

        response = TestClient(app).get(f"/prescriptions/{prescription_id}")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json().get("detail"), "Prescription not found")
        self.assertIsNotNone(fake_db.last_statement)

        compiled_sql = str(fake_db.last_statement)
        self.assertIn("prescriptions.user_id", compiled_sql)
        self.assertIn("prescriptions.id", compiled_sql)

    def test_detail_requires_authentication(self):
        app = self._build_app(_FakeDB(), None)

        response = TestClient(app).get(f"/prescriptions/{uuid.uuid4()}")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json().get("detail"), "Authentication required")


if __name__ == "__main__":
    unittest.main()
