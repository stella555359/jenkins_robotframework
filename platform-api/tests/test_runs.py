import sqlite3

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.schemas.run import RunCreateRequest
from app.services.run_service import run_create


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
        assert len(payload["run_id"].split("-")) == 2
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


def test_run_create_retries_with_next_sequence_on_conflict(monkeypatch) -> None:
    inserted_run_ids: list[str] = []

    def fake_insert(record: dict[str, str]) -> None:
        inserted_run_ids.append(record["run_id"])
        if len(inserted_run_ids) == 1:
            raise sqlite3.IntegrityError("UNIQUE constraint failed: runs.run_id")

    monkeypatch.setattr("app.services.run_service.insert_run_record", fake_insert)

    response = run_create(
        RunCreateRequest(
            testline="smoke",
            robotcase_path="cases/login.robot",
        )
    )

    assert len(inserted_run_ids[0].split("-")) == 2
    assert inserted_run_ids[1].endswith("-01")
    assert response.run_id.endswith("-01")
