from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from test_workflow_runner.cli import main as cli_main
from test_workflow_runner.config_resolver import EnvConfigResolver
from test_workflow_runner.models import HandlerResult, OrchestratorState
from test_workflow_runner.request_loader import RequestLoader, RequestValidationError
from test_workflow_runner.result_builder import ResultBuilder
from test_workflow_runner.runner import OrchestratorRunner


@pytest.fixture
def orchestrator_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    (repo_root / "configs").mkdir(parents=True)
    (repo_root / "testline_configuration").mkdir(parents=True)
    (repo_root / "scripts" / "traffic").mkdir(parents=True)
    (repo_root / "configs" / "env_map.json").write_text(
        json.dumps(
            {
                "T813": {
                    "config_id": "T813",
                    "config_path": "testline_configuration/T813.py",
                    "allowed_script_roots": ["scripts/traffic"],
                    "department": "RRM",
                    "site": "HZ",
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (repo_root / "testline_configuration" / "T813.py").write_text(
        "\n".join(
            [
                "class UE:",
                "    def __init__(self, ue_index, ue_type, label):",
                "        self.ue_index = ue_index",
                "        self.ue_type = ue_type",
                "        self.label = label",
                "        self.ue_ip = f'10.0.0.{ue_index}'",
                "",
                "class TL:",
                "    def __init__(self):",
                "        self.ues = [UE(1, 'phone', 'ue-1'), UE(2, 'phone', 'ue-2')]",
                "        self.gnbs = ['gnb-1']",
                "        self.enbs = []",
                "",
                "tl = TL()",
            ]
        ),
        encoding="utf-8",
    )
    return repo_root


def build_request_payload() -> dict:
    return {
        "testline": "7_5_UTE5G402T813",
        "ue_selection": {
            "selected_ues": [
                {"ue_index": 1, "ue_type": "phone", "label": "ue-1"},
                {"ue_index": 2, "ue_type": "phone", "label": "ue-2"},
            ]
        },
        "traffic_plan": {
            "stages": [
                {
                    "stage_id": 1,
                    "stage_name": "attach_and_observe",
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
                        },
                        {
                            "item_id": "syslog-1",
                            "model": "syslog_check",
                            "enabled": True,
                            "order": 20,
                            "execution_mode": "serial",
                            "continue_on_failure": False,
                            "ue_scope": {"mode": "all_selected_ues"},
                            "params": {"mode": "post_window_syslog_scan"},
                        },
                    ],
                },
                {
                    "stage_id": 2,
                    "stage_name": "traffic",
                    "execution_mode": "parallel",
                    "items": [
                        {
                            "item_id": "dl-1",
                            "model": "dl_traffic",
                            "enabled": True,
                            "order": 10,
                            "execution_mode": "parallel",
                            "continue_on_failure": False,
                            "ue_scope": {"mode": "all_selected_ues"},
                            "params": {"script_path": "scripts/traffic/dl.py"},
                        },
                        {
                            "item_id": "ul-1",
                            "model": "ul_traffic",
                            "enabled": True,
                            "order": 20,
                            "execution_mode": "parallel",
                            "continue_on_failure": False,
                            "ue_scope": {"mode": "all_selected_ues"},
                            "params": {"script_path": "scripts/traffic/ul.py"},
                        },
                    ],
                },
                {
                    "stage_id": 3,
                    "stage_name": "detach",
                    "execution_mode": "serial",
                    "items": [
                        {
                            "item_id": "detach-1",
                            "model": "detach",
                            "enabled": True,
                            "order": 10,
                            "execution_mode": "serial",
                            "continue_on_failure": True,
                            "ue_scope": {"mode": "all_selected_ues"},
                            "params": {},
                        }
                    ],
                },
            ]
        },
        "runtime_options": {
            "dry_run": True,
            "stop_on_failure": True,
            "max_parallel_workers": 4,
            "log_level": "INFO",
        },
    }


def test_request_loader_accepts_valid_payload(orchestrator_repo: Path) -> None:
    loader = RequestLoader(orchestrator_repo)
    request = loader.load_dict(build_request_payload())

    assert request.testline == "7_5_UTE5G402T813"
    assert request.testline_resolution.config_id == "T813"
    assert request.runtime_options.dry_run is True
    assert len(request.traffic_stages()) == 3


def test_request_loader_rejects_protected_parallel_stage(orchestrator_repo: Path) -> None:
    loader = RequestLoader(orchestrator_repo)
    payload = build_request_payload()
    payload["traffic_plan"]["stages"][0]["execution_mode"] = "parallel"
    payload["traffic_plan"]["stages"][0]["items"].append(
        {
            "item_id": "handover-1",
            "model": "handover",
            "enabled": True,
            "order": 30,
            "execution_mode": "parallel",
            "continue_on_failure": False,
            "ue_scope": {"mode": "all_selected_ues"},
            "params": {},
        }
    )
    payload["traffic_plan"]["stages"][0]["items"][0]["model"] = "swap"

    with pytest.raises(RequestValidationError):
        loader.load_dict(payload)


def test_orchestrator_runner_executes_dry_run_workflow(orchestrator_repo: Path) -> None:
    loader = RequestLoader(orchestrator_repo)
    request = loader.load_dict(build_request_payload())
    resolver = EnvConfigResolver(orchestrator_repo)
    context = resolver.load_testline_context(request.testline)
    runner = OrchestratorRunner()

    state = runner.execute(request, context, OrchestratorState())

    assert state.status == "completed"
    assert len(state.precondition_results) == 0
    assert len(state.traffic_results) == 4
    assert len(state.sidecar_results) == 1
    assert state.kpi_test_starttime is not None
    assert state.kpi_test_endtime is not None
    dl_result = next(item for item in state.traffic_results if item.model == "dl_traffic")
    ul_result = next(item for item in state.traffic_results if item.model == "ul_traffic")
    assert dl_result.summary["command"] == ["python", str((orchestrator_repo / "scripts" / "traffic" / "dl.py").resolve())]
    assert ul_result.summary["command"] == ["python", str((orchestrator_repo / "scripts" / "traffic" / "ul.py").resolve())]
    assert dl_result.summary["cwd"] == str(orchestrator_repo)
    assert ul_result.summary["cwd"] == str(orchestrator_repo)


def test_orchestrator_runner_supports_internal_followup_handlers_in_dry_run(orchestrator_repo: Path) -> None:
    loader = RequestLoader(orchestrator_repo)
    payload = build_request_payload()
    payload["traffic_plan"]["stages"].append(
        {
            "stage_id": 4,
            "stage_name": "followups",
            "execution_mode": "serial",
            "items": [
                {
                    "item_id": "generator-1",
                    "model": "kpi_generator",
                    "enabled": True,
                    "order": 10,
                    "execution_mode": "serial",
                    "continue_on_failure": False,
                    "ue_scope": {"mode": "all_selected_ues"},
                    "params": {
                        "build": "SBTS26R3.ENB.9999.260319.000005",
                        "environment": "T813.SCF.T813.gNB.25R3.20260224",
                        "scenario": "7UE_DL_Burst",
                        "template_names": ["Throughput"],
                        "report_timestamps_list": [["2026-04-22 10:00:00", "2026-04-22 10:05:00"]],
                    },
                },
                {
                    "item_id": "detector-1",
                    "model": "kpi_detector",
                    "enabled": True,
                    "order": 20,
                    "execution_mode": "serial",
                    "continue_on_failure": False,
                    "ue_scope": {"mode": "all_selected_ues"},
                    "params": {
                        "source_file": "artifacts/generated.xlsx",
                        "generate_html": True,
                    },
                },
            ],
        }
    )
    request = loader.load_dict(payload)
    resolver = EnvConfigResolver(orchestrator_repo)
    context = resolver.load_testline_context(request.testline)
    runner = OrchestratorRunner()

    state = runner.execute(request, context, OrchestratorState())

    assert state.status == "completed"
    assert len(state.followup_results) == 2
    assert [result.model for result in state.followup_results] == ["kpi_generator", "kpi_detector"]
    assert all(result.summary.get("implementation_mode") == "internal_api_dry_run" for result in state.followup_results)
    assert all(result.summary.get("environment") == "T813" for result in state.followup_results)
    assert all(result.summary.get("test_line") == "7_5_UTE5G402T813" for result in state.followup_results)


def test_cli_dry_run_writes_result_without_env_map(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    result_path = tmp_path / "result.json"
    request_path.write_text(json.dumps(build_request_payload(), indent=2), encoding="utf-8")

    exit_code = cli_main([str(request_path), "--dry-run", "--result-json", str(result_path)])

    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert result["status"] == "completed"
    assert result["testline"] == "7_5_UTE5G402T813"
    assert result["testline_alias"] == "T813"
    assert result["resolved_config"]["match_type"] == "dry_run_request"
    assert result["artifacts"]["result_json_path"] == str(result_path)
    assert result["artifact_manifest"][0]["kind"] == "workflow_request_json"
    assert result["artifact_manifest"][1]["kind"] == "workflow_result_json"
    assert result["timeline"][0]["event"] == "workflow_started"
    assert result["timeline"][-1]["event"] == "workflow_completed"
    assert any(entry.get("item_id") == "attach-1" for entry in result["timeline"])


def test_cli_dry_run_context_uses_repository_root_for_relative_script_paths(tmp_path: Path) -> None:
    request_path = tmp_path / "request.json"
    result_path = tmp_path / "result.json"
    request_path.write_text(json.dumps(build_request_payload(), indent=2), encoding="utf-8")

    exit_code = cli_main([
        str(request_path),
        "--dry-run",
        "--result-json",
        str(result_path),
        "--repository-root",
        str(tmp_path),
    ])

    result = json.loads(result_path.read_text(encoding="utf-8"))
    traffic_items = result["results"]["traffic"]
    dl_item = next(item for item in traffic_items if item["model"] == "dl_traffic")
    ul_item = next(item for item in traffic_items if item["model"] == "ul_traffic")

    assert exit_code == 0
    assert dl_item["summary"]["command"] == ["python", str((tmp_path / "scripts" / "traffic" / "dl.py").resolve())]
    assert ul_item["summary"]["command"] == ["python", str((tmp_path / "scripts" / "traffic" / "ul.py").resolve())]
    assert dl_item["summary"]["cwd"] == str(tmp_path)
    assert ul_item["summary"]["cwd"] == str(tmp_path)


def test_result_builder_adds_timeline_and_artifact_manifest(orchestrator_repo: Path) -> None:
    loader = RequestLoader(orchestrator_repo)
    request = loader.load_dict(build_request_payload())
    resolver = EnvConfigResolver(orchestrator_repo)
    context = resolver.load_testline_context(request.testline)
    state = OrchestratorState(
        status="completed",
        kpi_test_starttime="2026-04-22T10:00:00+08:00",
        kpi_test_endtime="2026-04-22T10:30:00+08:00",
        traffic_results=[
            HandlerResult(
                model="attach",
                status="completed",
                started_at="2026-04-22T10:00:01+08:00",
                completed_at="2026-04-22T10:00:20+08:00",
                stage_id=1,
                item_id="attach-1",
            )
        ],
        followup_results=[
            HandlerResult(
                model="kpi_generator",
                status="completed",
                started_at="2026-04-22T10:20:00+08:00",
                completed_at="2026-04-22T10:25:00+08:00",
                artifacts=[
                    {
                        "kind": "kpi_excel",
                        "label": "KPI workbook",
                        "path": "artifacts/kpi.xlsx",
                    }
                ],
                stage_id=90,
                item_id="generator-1",
            )
        ],
    )

    result = ResultBuilder().build_success(
        request,
        context,
        state,
        timestamps={"created_at": None, "started_at": state.kpi_test_starttime, "completed_at": state.kpi_test_endtime},
        artifacts={"request_json_path": "request.json", "result_json_path": "result.json", "extra_artifacts": []},
    )

    assert result["timeline"][0]["event"] == "workflow_started"
    assert result["timeline"][-1]["event"] == "workflow_completed"
    assert any(entry.get("item_id") == "generator-1" for entry in result["timeline"])
    assert result["artifact_manifest"][0]["kind"] == "workflow_request_json"
    assert result["artifact_manifest"][1]["kind"] == "workflow_result_json"
    kpi_artifact = next(item for item in result["artifact_manifest"] if item["kind"] == "kpi_excel")
    assert kpi_artifact["source"] == "kpi_generator"
    assert kpi_artifact["metadata"]["item_id"] == "generator-1"


def test_runner_routes_results_using_handler_bucket() -> None:
    runner = OrchestratorRunner()
    state = OrchestratorState()

    runner._append_result(
        state,
        HandlerResult(model="apply_preconditions", status="completed", started_at="t1", completed_at="t2"),
    )
    runner._append_result(
        state,
        HandlerResult(model="syslog_check", status="completed", started_at="t1", completed_at="t2"),
    )
    runner._append_result(
        state,
        HandlerResult(model="kpi_generator", status="completed", started_at="t1", completed_at="t2"),
    )
    runner._append_result(
        state,
        HandlerResult(model="attach", status="completed", started_at="t1", completed_at="t2"),
    )

    assert len(state.precondition_results) == 1
    assert len(state.sidecar_results) == 1
    assert len(state.followup_results) == 1
    assert len(state.traffic_results) == 1
