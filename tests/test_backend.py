from __future__ import annotations

import os
import unittest
from importlib.util import find_spec
from pathlib import Path

from test_support import temporary_directory


class BackendBoundaryTests(unittest.TestCase):
    def test_authentication_and_input_validation_without_database_access(self):
        from fastapi.testclient import TestClient
        from pydantic import SecretStr

        from apps.api.main import create_app
        from apps.api.settings import Settings

        token = "synthetic-test-token-used-only-in-test-process"
        settings = Settings(
            database_url=SecretStr("postgresql+psycopg://unused@127.0.0.1:1/unused"),
            backend_api_token=SecretStr(token),
        )
        with TestClient(create_app(settings)) as client:
            self.assertEqual(client.get("/api/v1/targets").status_code, 401)
            client.headers["Authorization"] = "Bearer wrong"
            self.assertEqual(client.get("/api/v1/health").status_code, 401)
            client.headers["Authorization"] = "Bearer " + token
            self.assertEqual(client.get("/api/v1/health").json(), {"status": "ok"})
            response = client.get("/api/v1/targets")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(len(response.json()), 4)
            for body in (
                {"target": "arbitrary"},
                {"target": "ecommerce", "budget": 201},
                {"target": "ecommerce", "strategy": "invalid"},
            ):
                self.assertEqual(
                    client.post("/api/v1/discovery-sessions", json=body).status_code, 422
                )
            self.assertEqual(
                client.post("/api/v1/discovery-sessions", content=b"x" * 4097).status_code, 413
            )


@unittest.skipUnless(
    find_spec("fastapi") and find_spec("sqlalchemy") and os.environ.get("DATABASE_URL"),
    "Backend dependencies and PostgreSQL test database are required",
)
class BackendTests(unittest.TestCase):
    def test_authentication_create_cancel_and_artifact_bounds(self):
        from fastapi.testclient import TestClient
        from pydantic import SecretStr

        from apps.api.main import create_app
        from apps.api.settings import Settings

        token = "synthetic-test-token-used-only-in-test-process"
        with temporary_directory() as folder:
            settings = Settings(
                database_url=SecretStr(os.environ["DATABASE_URL"]),
                backend_api_token=SecretStr(token),
                artifact_root=Path(folder),
                policy_file=Path("experiments/configs/registry.json"),
            )
            client = TestClient(create_app(settings))
            self.assertEqual(client.get("/api/v1/targets").status_code, 401)
            client.headers["Authorization"] = "Bearer " + token
            self.assertEqual(client.get("/api/v1/health").status_code, 200)
            self.assertEqual(
                client.post("/api/v1/discovery-sessions", json={"target": "arbitrary"}).status_code,
                422,
            )
            result = client.post(
                "/api/v1/discovery-sessions", json={"target": "ecommerce", "budget": 10}
            )
            self.assertEqual(result.status_code, 202)
            session = result.json()["id"]
            self.assertEqual(
                client.post(f"/api/v1/discovery-sessions/{session}/cancel", json={}).json()[
                    "status"
                ],
                "cancelled",
            )
            self.assertEqual(
                client.get(f"/api/v1/discovery-sessions/{session}/artifacts/sdk").status_code, 404
            )
            self.assertEqual(client.get("/api/v1/discovery-sessions/not-a-uuid").status_code, 422)
