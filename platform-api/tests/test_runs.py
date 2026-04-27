import allure

from app.schemas.run import RunCreateRequest
from app.repositories.run_repository import insert_run_record
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
    assert payload["executor_type"] == "robot"
    assert payload["status"] == "created"
    assert payload["message"] == "Run request accepted."

    row = fetch_run_record(payload["run_id"])

    assert row is not None
    assert row["run_id"] == payload["run_id"]
    assert row["executor_type"] == "robot"
    assert row["testline"] == "smoke"
    assert row["robotcase_path"] == "cases/login.robot"
    assert row["status"] == "created"
    assert row["message"] == "Run request accepted."
    assert row["workflow_spec_json"] == {}
    assert row["artifact_manifest_json"] == []
    assert row["kpi_summary_json"] == {}
    assert row["detector_summary_json"] == {}


@allure.feature("Run API")
@allure.story("Create run")
@allure.title("run_create retries with a sequence suffix on conflict")
def test_run_create_retries_with_next_sequence_on_conflict(monkeypatch) -> None:
    inserted_run_ids: list[str] = []

    def fake_insert(record: dict[str, str]) -> None:
        inserted_run_ids.append(record["run_id"])
        if len(inserted_run_ids) == 1:
            import sqlite3

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
@allure.story("Create run")
@allure.title("POST /api/runs supports python orchestrator workflows")
def test_create_python_orchestrator_run_persists_workflow_spec(client, fetch_run_record) -> None:
    response = client.post(
        "/api/runs",
        json={
            "testline": "T813",
            "executor_type": "python_orchestrator",
            "workflow_spec": {
                "name": "Attach Operate Detach",
                "stages": [
                    {
                        "stage_id": 1,
                        "stage_name": "attach",
                        "execution_mode": "serial",
                        "items": [
                            {
                                "item_id": "attach-1",
                                "model": "attach",
                                "enabled": True,
                                "order": 10,
                                "execution_mode": "serial",
                                "continue_on_failure": False,
                                "ue_scope": {"mode": "all_selected_ues"},
                                "params": {"attach_timeout_seconds": 120},
                            }
                        ],
                    }
                ],
                "runtime_options": {"dry_run": True},
                "portal_followups": {"auto_generator": True},
            },
            "enable_kpi_generator": True,
            "enable_kpi_anomaly_detector": True,
            "kpi_config": {
                "source_type": "compass",
                "template_set": "ivy_26R2_vdt",
                "environment": "T813",
                "scenario": "7UE_DL_Burst",
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["executor_type"] == "python_orchestrator"

    row = fetch_run_record(payload["run_id"])

    assert row is not None
    assert row["workflow_name"] == "Attach Operate Detach"
    assert row["workflow_spec_json"]["name"] == "Attach Operate Detach"
    assert row["workflow_spec_json"]["stages"][0]["items"][0]["model"] == "attach"
    assert row["enable_kpi_generator"] is True
    assert row["enable_kpi_anomaly_detector"] is True
    assert row["kpi_config_json"]["template_set"] == "ivy_26R2_vdt"


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
        assert item["executor_type"] == "robot"
        assert item["status"] == "created"
        assert item["message"] == "Run request accepted."
        assert item["enable_kpi_generator"] is False
        assert item["enable_kpi_anomaly_detector"] is False
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
    assert payload["executor_type"] == "robot"
    assert payload["testline"] == "smoke"
    assert payload["robotcase_path"] == "cases/login.robot"
    assert payload["status"] == "created"
    assert payload["message"] == "Run request accepted."
    assert payload["artifact_manifest"] == []
    assert payload["kpi_summary"] == {}
    assert payload["detector_summary"] == {}
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

    assert payload["run_id"] == persisted_record["run_id"]
    assert payload["executor_type"] == persisted_record["executor_type"]
    assert payload["testline"] == persisted_record["testline"]
    assert payload["robotcase_path"] == persisted_record["robotcase_path"]
    assert payload["status"] == persisted_record["status"]
    assert payload["message"] == persisted_record["message"]
    assert payload["artifact_manifest"] == persisted_record["artifact_manifest_json"]
    assert payload["kpi_summary"] == persisted_record["kpi_summary_json"]
    assert payload["detector_summary"] == persisted_record["detector_summary_json"]


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

    for key in matching_item:
        assert matching_item[key] == detail_payload[key]


@allure.feature("Run API")
@allure.story("Run detail")
@allure.title("GET /api/runs/{run_id} supports run IDs with numeric suffixes")
def test_get_run_detail_supports_suffixed_run_ids(client) -> None:
    insert_run_record(
        {
            "run_id": "run-20260422104958123-01",
            "executor_type": "robot",
            "workflow_name": "cases/login.robot",
            "testline": "smoke",
            "robotcase_path": "cases/login.robot",
            "build": "",
            "scenario": "",
            "status": "created",
            "message": "Run request accepted.",
            "enable_kpi_generator": False,
            "enable_kpi_anomaly_detector": False,
            "workflow_spec_json": {},
            "run_metadata_json": {},
            "artifact_manifest_json": [],
            "kpi_config_json": {},
            "kpi_summary_json": {},
            "detector_summary_json": {},
            "jenkins_build_ref": "",
            "started_at": "",
            "finished_at": "",
            "created_at": "2026-04-22T10:49:58.123+08:00",
            "updated_at": "2026-04-22T10:49:58.123+08:00",
        }
    )

    response = client.get("/api/runs/run-20260422104958123-01")

    assert response.status_code == 200

    payload = response.json()

    assert payload["run_id"] == "run-20260422104958123-01"
    assert payload["testline"] == "smoke"
    assert payload["robotcase_path"] == "cases/login.robot"


@allure.feature("Run API")
@allure.story("Workflow validation")
@allure.title("POST /api/runs rejects python orchestrator runs without workflow_spec")
def test_create_python_orchestrator_run_requires_workflow_spec(client) -> None:
    response = client.post(
        "/api/runs",
        json={
            "testline": "T813",
            "executor_type": "python_orchestrator",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "workflow_spec is required when executor_type is python_orchestrator."


@allure.feature("Run API")
@allure.story("Workflow validation")
@allure.title("POST /api/runs rejects robot runs without robotcase_path")
def test_create_robot_run_requires_robotcase_path(client) -> None:
    response = client.post(
        "/api/runs",
        json={
            "testline": "smoke",
            "executor_type": "robot",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "robotcase_path is required when executor_type is robot."


@allure.feature("Run API")
@allure.story("Workflow validation")
@allure.title("POST /api/runs rejects KPI options in robot mode")
def test_create_robot_run_rejects_kpi_options(client) -> None:
    response = client.post(
        "/api/runs",
        json={
            "testline": "smoke",
            "executor_type": "robot",
            "robotcase_path": "cases/login.robot",
            "enable_kpi_generator": True,
            "kpi_config": {
                "scenario": "7UE_DL_Burst",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "KPI options are only supported when executor_type is python_orchestrator."


@allure.feature("Run API")
@allure.story("Run callbacks")
@allure.title("Jenkins callback updates artifacts and KPI summaries")
def test_jenkins_callback_updates_artifacts_and_kpi_summary(client, create_run_via_api) -> None:
    created_run = create_run_via_api(
        "T813",
        "",
        executor_type="python_orchestrator",
        workflow_spec={
            "name": "kpi-regression",
            "stages": [],
            "runtime_options": {},
            "portal_followups": {},
        },
        enable_kpi_generator=True,
        enable_kpi_anomaly_detector=True,
    )
    run_id = created_run["run_id"]

    callback_response = client.post(
        f"/api/runs/{run_id}/callbacks/jenkins",
        json={
            "status": "completed",
            "message": "Pipeline completed.",
            "jenkins_build_ref": "gnb-kpi-regression#42",
            "started_at": "2026-04-23T09:00:00+08:00",
            "finished_at": "2026-04-23T09:30:00+08:00",
            "artifact_manifest": [
                {
                    "kind": "kpi_excel",
                    "label": "KPI workbook",
                    "path": "artifacts/kpi.xlsx",
                    "url": "https://jenkins.local/job/42/artifact/kpi.xlsx",
                },
                {
                    "kind": "detector_html",
                    "label": "Detector report",
                    "path": "artifacts/detector.html",
                    "url": "https://jenkins.local/job/42/artifact/detector.html",
                },
            ],
            "kpi_summary": {"counter_count": 182, "window": "09:00-09:30"},
            "detector_summary": {"anomaly_count": 3, "top_counter": "RRC_SUCCESS_RATE"},
            "metadata": {"pipeline_stage": "callback_platform_api"},
        },
    )

    assert callback_response.status_code == 200
    assert callback_response.json()["status"] == "completed"

    detail_response = client.get(f"/api/runs/{run_id}")
    artifacts_response = client.get(f"/api/runs/{run_id}/artifacts")
    kpi_response = client.get(f"/api/runs/{run_id}/kpi")

    assert detail_response.status_code == 200
    assert artifacts_response.status_code == 200
    assert kpi_response.status_code == 200

    detail_payload = detail_response.json()
    artifacts_payload = artifacts_response.json()
    kpi_payload = kpi_response.json()

    assert detail_payload["status"] == "completed"
    assert detail_payload["workflow_spec"]["name"] == "kpi-regression"
    assert detail_payload["enable_kpi_generator"] is True
    assert detail_payload["enable_kpi_anomaly_detector"] is True
    assert detail_payload["jenkins_build_ref"] == "gnb-kpi-regression#42"
    assert detail_payload["artifact_manifest"][0]["kind"] == "kpi_excel"
    assert detail_payload["kpi_summary"]["counter_count"] == 182
    assert detail_payload["detector_summary"]["anomaly_count"] == 3
    assert detail_payload["metadata"]["pipeline_stage"] == "callback_platform_api"

    assert len(artifacts_payload["items"]) == 2
    assert kpi_payload["generator_enabled"] is True
    assert kpi_payload["detector_enabled"] is True
    assert kpi_payload["artifact_manifest"][1]["kind"] == "detector_html"
    assert kpi_payload["detector_summary"]["top_counter"] == "RRC_SUCCESS_RATE"


@allure.feature("Run API")
@allure.story("Run callbacks")
@allure.title("Jenkins callback returns 404 for a missing run")
def test_jenkins_callback_returns_404_for_missing_run(client) -> None:
    response = client.post(
        "/api/runs/run-unknown/callbacks/jenkins",
        json={
            "status": "completed",
            "message": "Pipeline completed.",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found."}


@allure.feature("Run API")
@allure.story("Run metadata")
@allure.title("GET /api/runs/{run_id}/artifacts returns 404 for a missing run")
def test_get_run_artifacts_returns_404_for_missing_run(client) -> None:
    response = client.get("/api/runs/run-unknown/artifacts")

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found."}


@allure.feature("Run API")
@allure.story("Run metadata")
@allure.title("GET /api/runs/{run_id}/kpi returns 404 for a missing run")
def test_get_run_kpi_returns_404_for_missing_run(client) -> None:
    response = client.get("/api/runs/run-unknown/kpi")

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found."}
