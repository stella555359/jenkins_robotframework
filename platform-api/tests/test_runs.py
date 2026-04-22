import sqlite3

import allure

from app.schemas.run import RunCreateRequest
from app.services.run_service import run_create


@allure.feature("Run API")
@allure.story("Create run")
@allure.title("POST /api/runs persists a run record")
def test_create_run_persists_record(client, fetch_run_record) -> None:
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

    row = fetch_run_record(payload["run_id"])

    assert row is not None
    assert row["run_id"] == payload["run_id"]
    assert row["testline"] == "smoke"
    assert row["robotcase_path"] == "cases/login.robot"
    assert row["status"] == "created"
    assert row["message"] == "Run request accepted."


@allure.feature("Run API")
@allure.story("Create run")
@allure.title("run_create retries with a sequence suffix on conflict")
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


@allure.feature("Run API")
@allure.story("List runs")
@allure.title("GET /api/runs returns latest runs first")
def test_list_runs_returns_latest_first(client, create_run_via_api) -> None:
    create_run_via_api("smoke", "cases/login.robot")
    create_run_via_api("regression", "cases/payment.robot")
    response = client.get("/api/runs")

    assert response.status_code == 200

    payload = response.json()

    assert len(payload["items"]) == 2
    assert payload["items"][0]["testline"] == "regression"
    assert payload["items"][0]["robotcase_path"] == "cases/payment.robot"
    assert payload["items"][1]["testline"] == "smoke"
    assert payload["items"][1]["robotcase_path"] == "cases/login.robot"

    for item in payload["items"]:
        assert item["run_id"].startswith("run-")
        assert item["status"] == "created"
        assert item["message"] == "Run request accepted."
        assert "created_at" in item
        assert "updated_at" in item


@allure.feature("Run API")
@allure.story("Run detail")
@allure.title("GET /api/runs/{run_id} returns the expected run detail")
def test_get_run_detail_returns_expected_record(client, create_run_via_api) -> None:
    created_run = create_run_via_api("smoke", "cases/login.robot")
    run_id = created_run["run_id"]
    response = client.get(f"/api/runs/{run_id}")

    assert response.status_code == 200

    payload = response.json()

    assert payload["run_id"] == run_id
    assert payload["testline"] == "smoke"
    assert payload["robotcase_path"] == "cases/login.robot"
    assert payload["status"] == "created"
    assert payload["message"] == "Run request accepted."
    assert "created_at" in payload
    assert "updated_at" in payload


@allure.feature("Run API")
@allure.story("Run detail")
@allure.title("GET /api/runs/{run_id} matches the persisted SQLite record")
def test_get_run_detail_matches_persisted_record(client, create_run_via_api, fetch_run_record) -> None:
    created_run = create_run_via_api("smoke", "cases/login.robot")
    run_id = created_run["run_id"]
    persisted_record = fetch_run_record(run_id)
    response = client.get(f"/api/runs/{run_id}")

    assert persisted_record is not None
    assert response.status_code == 200

    payload = response.json()

    assert payload == persisted_record


@allure.feature("Run API")
@allure.story("Run detail")
@allure.title("GET /api/runs/{run_id} returns 404 for a missing run")
def test_get_run_detail_returns_404_for_missing_run(client) -> None:
    response = client.get("/api/runs/run-unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found."}


@allure.feature("Run API")
@allure.story("Run detail")
@allure.title("GET /api/runs/{run_id} stays consistent with GET /api/runs")
def test_run_list_and_detail_are_consistent(client, create_run_via_api) -> None:
    created_run = create_run_via_api("smoke", "cases/login.robot")
    run_id = created_run["run_id"]

    list_response = client.get("/api/runs")
    detail_response = client.get(f"/api/runs/{run_id}")

    assert list_response.status_code == 200
    assert detail_response.status_code == 200

    list_payload = list_response.json()
    detail_payload = detail_response.json()

    matching_item = next(item for item in list_payload["items"] if item["run_id"] == run_id)

    assert matching_item == detail_payload


@allure.feature("Run API")
@allure.story("Run detail")
@allure.title("GET /api/runs/{run_id} supports run IDs with numeric suffixes")
def test_get_run_detail_supports_suffixed_run_ids(client, db_connection) -> None:
    db_connection.execute(
        """
        INSERT INTO runs (
            run_id,
            testline,
            robotcase_path,
            status,
            message,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "run-20260422104958123-01",
            "smoke",
            "cases/login.robot",
            "created",
            "Run request accepted.",
            "2026-04-22T10:49:58.123+08:00",
            "2026-04-22T10:49:58.123+08:00",
        ),
    )
    db_connection.commit()

    response = client.get("/api/runs/run-20260422104958123-01")

    assert response.status_code == 200

    payload = response.json()

    assert payload["run_id"] == "run-20260422104958123-01"
    assert payload["testline"] == "smoke"
    assert payload["robotcase_path"] == "cases/login.robot"
