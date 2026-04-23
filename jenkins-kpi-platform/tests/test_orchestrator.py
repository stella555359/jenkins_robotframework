from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gnb_kpi_orchestrator.config_resolver import EnvConfigResolver
from gnb_kpi_orchestrator.models import OrchestratorState
from gnb_kpi_orchestrator.request_loader import RequestLoader, RequestValidationError
from gnb_kpi_orchestrator.runner import OrchestratorRunner


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
        "env": "T813",
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

    assert request.env == "T813"
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
    context = resolver.load_testline_context(request.env)
    runner = OrchestratorRunner()

    state = runner.execute(request, context, OrchestratorState())

    assert state.status == "completed"
    assert len(state.precondition_results) == 0
    assert len(state.traffic_results) == 4
    assert len(state.sidecar_results) == 1
    assert state.kpi_test_starttime is not None
    assert state.kpi_test_endtime is not None


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
    context = resolver.load_testline_context(request.env)
    runner = OrchestratorRunner()

    state = runner.execute(request, context, OrchestratorState())

    assert state.status == "completed"
    assert len(state.followup_results) == 2
    assert [result.model for result in state.followup_results] == ["kpi_generator", "kpi_detector"]
    assert all(result.summary.get("implementation_mode") == "internal_api_dry_run" for result in state.followup_results)
