import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.repositories.run_repository import get_run_record_by_id


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
    def _create_run(
        testline: str = "smoke",
        robotcase_path: str = "cases/login.robot",
        *,
        executor_type: str = "robot",
        workflow_spec: dict | None = None,
        enable_kpi_generator: bool = False,
        enable_kpi_anomaly_detector: bool = False,
    ) -> dict:
        payload = {
            "testline": testline,
            "executor_type": executor_type,
            "enable_kpi_generator": enable_kpi_generator,
            "enable_kpi_anomaly_detector": enable_kpi_anomaly_detector,
        }
        if robotcase_path:
            payload["robotcase_path"] = robotcase_path
        if workflow_spec is not None:
            payload["workflow_spec"] = workflow_spec
        response = client.post(
            "/api/runs",
            json=payload,
        )

        assert response.status_code == 200
        return response.json()

    return _create_run


@pytest.fixture
def fetch_run_record(db_connection: sqlite3.Connection) -> Callable[[str], dict | None]:
    def _fetch(run_id: str) -> dict | None:
        return get_run_record_by_id(run_id)

    return _fetch
