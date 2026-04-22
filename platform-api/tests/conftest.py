import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def isolated_runs_db(tmp_path: Path) -> Iterator[str]:
    original_db_path = settings.runs_db_path
    db_path = str(tmp_path / "automation_platform.db")
    settings.runs_db_path = db_path

    try:
        yield db_path
    finally:
        settings.runs_db_path = original_db_path


@pytest.fixture
def client(isolated_runs_db: str) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def db_connection(isolated_runs_db: str) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(isolated_runs_db)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def create_run_via_api(client: TestClient) -> Callable[[str, str], dict]:
    def _create_run(testline: str = "smoke", robotcase_path: str = "cases/login.robot") -> dict:
        response = client.post(
            "/api/runs",
            json={
                "testline": testline,
                "robotcase_path": robotcase_path,
            },
        )

        assert response.status_code == 200
        return response.json()

    return _create_run


@pytest.fixture
def fetch_run_record(db_connection: sqlite3.Connection) -> Callable[[str], dict | None]:
    def _fetch(run_id: str) -> dict | None:
        row = db_connection.execute(
            """
            SELECT
                run_id,
                testline,
                robotcase_path,
                status,
                message,
                created_at,
                updated_at
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

        return dict(row) if row else None

    return _fetch
