import allure

from app.repositories.ai_analysis_repository import get_latest_ai_analysis_record
from app.services.ai_analysis_worker import process_next_ai_analysis


@allure.feature("AI Analysis")
@allure.story("AI analysis contract")
@allure.title("GET /api/runs/{run_id}/ai-analysis returns 404 before generation")
def test_get_ai_analysis_returns_404_before_generation(client, create_run_via_api) -> None:
    run = create_run_via_api()

    response = client.get(f"/api/runs/{run['run_id']}/ai-analysis")

    assert response.status_code == 404
    assert response.json() == {"detail": "AI analysis not generated."}


@allure.feature("AI Analysis")
@allure.story("AI analysis contract")
@allure.title("POST /api/runs/{run_id}/ai-analysis returns 404 for a missing run")
def test_create_ai_analysis_returns_404_for_missing_run(client) -> None:
    response = client.post(
        "/api/runs/run-unknown/ai-analysis",
        json={"refresh": True, "analysis_mode": "rules_first"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found."}


@allure.feature("AI Analysis")
@allure.story("AI analysis contract")
@allure.title("POST /api/runs/{run_id}/ai-analysis queues an analysis record")
def test_create_ai_analysis_queues_record(client, create_run_via_api, tmp_path) -> None:
    run = create_run_via_api()
    run_id = run["run_id"]
    log_path = tmp_path / "console.log"
    log_path.write_text("Permission denied (publickey)", encoding="utf-8")

    client.post(
        f"/api/runs/{run_id}/callbacks/jenkins",
        json={
            "status": "failed",
            "message": "Pipeline failed.",
            "jenkins_build_ref": "robot/robot-execution#42",
            "artifact_manifest": [
                {
                    "kind": "jenkins_console",
                    "label": "Console",
                    "path": str(log_path),
                }
            ],
        },
    )

    response = client.post(
        f"/api/runs/{run_id}/ai-analysis",
        json={"refresh": True, "analysis_mode": "rules_first", "include_console": True, "include_artifacts": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["analysis_id"].startswith(f"ai-{run_id}-")
    assert payload["analysis_status"] == "queued"

    record = get_latest_ai_analysis_record(run_id)
    assert record is not None
    assert record["analysis_status"] == "queued"
    assert record["analysis_mode"] == "rules_first"
    assert record["request_json"]["include_artifacts"] is True
    assert any(ref["kind"] == "jenkins_console" for ref in record["result_json"]["input_refs"])


@allure.feature("AI Analysis")
@allure.story("AI analysis contract")
@allure.title("POST /api/runs/{run_id}/ai-analysis defaults to rules-first mode")
def test_create_ai_analysis_defaults_to_rules_first(client, create_run_via_api) -> None:
    run = create_run_via_api()
    run_id = run["run_id"]

    response = client.post(
        f"/api/runs/{run_id}/ai-analysis",
        json={"refresh": True, "include_console": True, "include_artifacts": True},
    )

    assert response.status_code == 200
    record = get_latest_ai_analysis_record(run_id)
    assert record is not None
    assert record["analysis_mode"] == "rules_first"
    assert record["request_json"]["analysis_mode"] == "rules_first"


@allure.feature("AI Analysis")
@allure.story("AI analysis contract")
@allure.title("GET /api/runs/{run_id}/ai-analysis returns queued analysis result")
def test_get_ai_analysis_returns_queued_result(client, create_run_via_api) -> None:
    run = create_run_via_api()
    run_id = run["run_id"]
    create_response = client.post(
        f"/api/runs/{run_id}/ai-analysis",
        json={"refresh": True, "analysis_mode": "rules_first"},
    )
    analysis_id = create_response.json()["analysis_id"]

    response = client.get(f"/api/runs/{run_id}/ai-analysis")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["analysis_id"] == analysis_id
    assert payload["analysis_status"] == "queued"
    assert payload["log_summary"]["one_line_summary"] == "AI analysis is queued."


@allure.feature("AI Analysis")
@allure.story("AI report")
@allure.title("GET /api/runs/{run_id}/ai-report returns markdown content")
def test_get_ai_report_returns_markdown(client, create_run_via_api) -> None:
    run = create_run_via_api()
    run_id = run["run_id"]
    client.post(
        f"/api/runs/{run_id}/ai-analysis",
        json={"refresh": True, "analysis_mode": "rules_first"},
    )

    response = client.get(f"/api/runs/{run_id}/ai-report")

    assert response.status_code == 200
    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["report_format"] == "markdown"
    assert "# AI Run Analysis Report" in payload["content"]


@allure.feature("AI Analysis")
@allure.story("AI worker")
@allure.title("AI worker processes a rules-first queued analysis")
def test_ai_worker_processes_rules_first_analysis(client, create_run_via_api, tmp_path) -> None:
    run = create_run_via_api()
    run_id = run["run_id"]
    log_path = tmp_path / "console.log"
    log_path.write_text("Git failed: Permission denied (publickey)", encoding="utf-8")

    callback_response = client.post(
        f"/api/runs/{run_id}/callbacks/jenkins",
        json={
            "status": "failed",
            "message": "Prepare Workspace failed.",
            "jenkins_build_ref": "robot/robot-execution#42",
            "artifact_manifest": [
                {
                    "kind": "jenkins_console",
                    "label": "Console",
                    "path": str(log_path),
                }
            ],
            "metadata": {
                "pipeline_stages": [
                    {"name": "Prepare Workspace", "status": "failed"},
                ]
            },
        },
    )
    assert callback_response.status_code == 200

    create_response = client.post(
        f"/api/runs/{run_id}/ai-analysis",
        json={"refresh": True, "analysis_mode": "rules_first", "include_artifacts": True},
    )
    assert create_response.status_code == 200

    assert process_next_ai_analysis() is True

    response = client.get(f"/api/runs/{run_id}/ai-analysis")
    payload = response.json()
    assert response.status_code == 200
    assert payload["analysis_status"] == "completed"
    assert payload["root_cause"]["category"] == "scm_credentials"
    assert payload["root_cause"]["confidence"] == "medium"
    assert payload["root_cause"]["recommended_actions"]
