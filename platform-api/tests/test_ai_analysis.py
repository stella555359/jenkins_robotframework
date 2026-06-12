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


@allure.feature("AI Analysis")
@allure.story("AI worker")
@allure.title("rules-first v2 uses output.xml as primary diagnostic evidence")
def test_ai_worker_rules_first_v2_extracts_robot_output_diagnosis(client, create_run_via_api, tmp_path) -> None:
    run = create_run_via_api()
    run_id = run["run_id"]
    output_xml = tmp_path / "output.xml"
    debug_log = tmp_path / "debug.log"
    robot_command = tmp_path / "robot-command.json"
    callback_payload = tmp_path / "callback-payload.json"
    output_xml.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<robot>
  <suite name="Smoke">
    <test name="Attach UE">
      <kw name="Wait Until UE Is Attached">
        <status status="FAIL">Timeout waiting for UE attached state</status>
      </kw>
      <status status="FAIL">Timeout waiting for UE attached state</status>
    </test>
    <status status="FAIL"/>
  </suite>
</robot>
""",
        encoding="utf-8",
    )
    debug_log.write_text("ERROR Timeout waiting for UE attached state", encoding="utf-8")
    robot_command.write_text('{"command": "python -m robot -t Attach UE tests.robot"}', encoding="utf-8")
    callback_payload.write_text('{"status": "failed", "message": "Robot failed", "artifact_manifest": []}', encoding="utf-8")

    callback_response = client.post(
        f"/api/runs/{run_id}/callbacks/jenkins",
        json={
            "status": "failed",
            "message": "Robot failed.",
            "artifact_manifest": [
                {"kind": "robot_output", "label": "output.xml", "path": str(output_xml)},
                {"kind": "robot_debug", "label": "debug.log", "path": str(debug_log)},
                {"kind": "robot_command", "label": "robot-command.json", "path": str(robot_command)},
                {"kind": "callback_payload", "label": "callback-payload.json", "path": str(callback_payload)},
            ],
        },
    )
    assert callback_response.status_code == 200

    create_response = client.post(
        f"/api/runs/{run_id}/ai-analysis",
        json={"refresh": True, "analysis_mode": "rules_first", "include_artifacts": True, "include_console": False},
    )
    assert create_response.status_code == 200

    assert process_next_ai_analysis() is True

    response = client.get(f"/api/runs/{run_id}/ai-analysis")
    payload = response.json()
    assert response.status_code == 200
    assert payload["analysis_status"] == "completed"
    assert payload["root_cause"]["category"] == "timeout"
    assert payload["quality_signals"]["failure_layer"] == "robot"
    assert payload["quality_signals"]["matched_rule"] == "robot_keyword_timeout"
    assert payload["quality_signals"]["rerun_advice"] == "needs_human_check"
    assert payload["root_cause"]["evidence"][0]["source"] == "output.xml"
    assert "Attach UE" in payload["root_cause"]["symptom"]
    assert "Wait Until UE Is Attached" in payload["root_cause"]["symptom"]


@allure.feature("AI Analysis")
@allure.story("AI worker")
@allure.title("rules-first v2 classifies Robot library import failures")
def test_ai_worker_rules_first_v2_classifies_taf_import_error(client, create_run_via_api, tmp_path) -> None:
    run = create_run_via_api()
    run_id = run["run_id"]
    output_xml = tmp_path / "output.xml"
    output_xml.write_text(
        """<robot>
  <suite name="Smoke">
    <test name="Import resources">
      <status status="FAIL">Importing library failed: No module named taf.namespaces.fake</status>
    </test>
  </suite>
</robot>
""",
        encoding="utf-8",
    )

    callback_response = client.post(
        f"/api/runs/{run_id}/callbacks/jenkins",
        json={
            "status": "failed",
            "message": "Robot import failed.",
            "artifact_manifest": [
                {"kind": "robot_output", "label": "output.xml", "path": str(output_xml)},
            ],
        },
    )
    assert callback_response.status_code == 200

    create_response = client.post(
        f"/api/runs/{run_id}/ai-analysis",
        json={"refresh": True, "analysis_mode": "rules_first", "include_artifacts": True, "include_console": False},
    )
    assert create_response.status_code == 200

    assert process_next_ai_analysis() is True

    response = client.get(f"/api/runs/{run_id}/ai-analysis")
    payload = response.json()
    assert response.status_code == 200
    assert payload["analysis_status"] == "completed"
    assert payload["root_cause"]["category"] == "taf_import_or_library_error"
    assert payload["quality_signals"]["failure_layer"] == "taf"
    assert payload["quality_signals"]["matched_rule"] == "robot_taf_import_or_keyword_error"
