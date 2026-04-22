import sqlite3

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


def test_create_run_persists_record(tmp_path) -> None:
    original_db_path = settings.runs_db_path
    settings.runs_db_path = str(tmp_path / "automation_platform.db")

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/runs",
                json={
                    "testline": "smoke",
                    "robotcase_path": "cases/login.robot",
                },
            )

        assert response.status_code == 200
        payload = response.json()

        assert payload["run_id"].startswith("run-")
        assert payload["status"] == "created"
        assert payload["message"] == "Run request accepted."

        with sqlite3.connect(settings.runs_db_path) as connection:
            row = connection.execute(
                """
                SELECT run_id, testline, robotcase_path, status, message
                FROM runs
                WHERE run_id = ?
                """,
                (payload["run_id"],),
            ).fetchone()

        assert row == (
            payload["run_id"],
            "smoke",
            "cases/login.robot",
            "created",
            "Run request accepted.",
        )
    finally:
        settings.runs_db_path = original_db_path
