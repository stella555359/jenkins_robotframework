import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_robot_command.py"
SPEC = importlib.util.spec_from_file_location("build_robot_command", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC is not None and SPEC.loader is not None
SPEC.loader.exec_module(MODULE)

build_robot_command_plan = MODULE.build_robot_command_plan


def test_build_robot_command_resolves_robotws_relative_case(tmp_path: Path) -> None:
    robotws_case = tmp_path / "robotws" / "testsuite" / "smoke" / "login.robot"
    robotws_case.parent.mkdir(parents=True)
    robotws_case.write_text("*** Test Cases ***\nSmoke\n    No Operation\n", encoding="utf-8")
    (tmp_path / "testline_configuration" / "7_5_UTE5G402T813").mkdir(parents=True)

    plan = build_robot_command_plan(
        {
            "run_id": "run-robot-1",
            "testline": "7_5_UTE5G402T813",
            "robotcase_path": "testsuite/smoke/login.robot",
        },
        workspace_root=tmp_path,
    )

    assert plan["command"][0:3] == ["python", "-m", "robot"]
    assert plan["command"][3:5] == ["--pythonpath", str((tmp_path / "robotws").resolve())]
    assert plan["command"][-1] == str(robotws_case.resolve())
    assert "-V" in plan["command"]
    assert str((tmp_path / "testline_configuration" / "7_5_UTE5G402T813").resolve()) in plan["command"]
    assert plan["resolved_paths"]["output_dir"] == str((tmp_path / "artifacts" / "quicktest" / "retry-0" / "login").resolve())
    assert "set -euo pipefail" in plan["shell"]["shell_script_text"]


def test_build_robot_command_prefers_workspace_relative_case(tmp_path: Path) -> None:
    workspace_case = tmp_path / "cases" / "login.robot"
    workspace_case.parent.mkdir(parents=True)
    workspace_case.write_text("*** Test Cases ***\nSmoke\n    No Operation\n", encoding="utf-8")
    (tmp_path / "testline_configuration" / "smoke").mkdir(parents=True)

    plan = build_robot_command_plan(
        {
            "testline": "smoke",
            "robotcase_path": "cases/login.robot",
            "case_name": "Smoke Login",
            "variables": {"BUILD": "SBTS26R2"},
        },
        workspace_root=tmp_path,
    )

    assert plan["command"][-1] == str(workspace_case.resolve())
    assert "-t" in plan["command"]
    assert "Smoke Login" in plan["command"]
    assert "-v" in plan["command"]
    assert "BUILD:SBTS26R2" in plan["command"]
    assert plan["execution"]["selected_tests"] == ["Smoke Login"]


def test_build_robot_command_rejects_missing_case_path(tmp_path: Path) -> None:
    (tmp_path / "testline_configuration" / "smoke").mkdir(parents=True)

    with pytest.raises(FileNotFoundError):
        build_robot_command_plan(
            {
                "testline": "smoke",
                "robotcase_path": "testsuite/missing.robot",
            },
            workspace_root=tmp_path,
        )


def test_build_robot_command_supports_legacy_jenkins_payload_shape(tmp_path: Path) -> None:
    robotws_case = tmp_path / "robotws" / "testsuite" / "Hangzhou" / "RRM" / "RAN_PZ_HAZ_34" / "CB007949" / "ca_cases.robot"
    robotws_case.parent.mkdir(parents=True)
    robotws_case.write_text("*** Test Cases ***\nLegacy\n    No Operation\n", encoding="utf-8")
    (tmp_path / "testline_configuration" / "7_5_UTE5G402T820").mkdir(parents=True)

    python_env_root = tmp_path / "CIENV" / "7_5_UTE5G402T820"
    (python_env_root / "bin").mkdir(parents=True)
    (python_env_root / "bin" / "activate").write_text("# test activate\n", encoding="utf-8")

    plan = build_robot_command_plan(
        {
            "dryrunMode": False,
            "robotPath": str((tmp_path / "robotws").resolve()),
            "pkgPath": "http://10.101.54.7/SBTS00/release.zip -v target_version:SBTS00_ENB_9999_260425_000006 -v testline_name:7_5_UTE5G402T820 -v caseBranch:master",
            "robotSuites": "-t '?1?CB007949_D_Extend_02_TDD_3CC_CA_Interworking_with_VoNR' -t '?1?CB007922_A_24_NSA_ Single_UE_Peak_Throughput_100M_60M_1116_0ms_beamset_3_1' robotws/testsuite/Hangzhou/RRM/RAN_PZ_HAZ_34/CB007949/ca_cases.robot",
            "configPath": "testline_configuration/7_5_UTE5G402T820",
            "pythonPath": str(python_env_root.resolve()),
            "retryTimes": "0",
        },
        workspace_root=tmp_path,
    )

    assert plan["metadata"]["variables"]["AF_PATH"] == "http://10.101.54.7/SBTS00/release.zip"
    assert plan["metadata"]["variables"]["target_version"] == "SBTS00_ENB_9999_260425_000006"
    assert plan["execution"]["selected_tests"] == [
        "?1?CB007949_D_Extend_02_TDD_3CC_CA_Interworking_with_VoNR",
        "?1?CB007922_A_24_NSA_ Single_UE_Peak_Throughput_100M_60M_1116_0ms_beamset_3_1",
    ]
    assert plan["resolved_paths"]["activate_script"] == str((python_env_root / "bin" / "activate").resolve())
    assert plan["resolved_paths"]["output_dir"] == str((tmp_path / "artifacts" / "quicktest" / "retry-0" / "ca_cases").resolve())
    assert ". " + str((python_env_root / "bin" / "activate").resolve()) in plan["shell"]["shell_script_text"]
    assert "export http_proxy=''" in plan["shell"]["shell_script_text"]
    assert "-x quicktest.xml" in plan["command_text"]


def test_build_robot_command_ignores_legacy_uuf_source_field(tmp_path: Path) -> None:
    robotws_case = tmp_path / "robotws" / "testsuite" / "smoke" / "login.robot"
    robotws_case.parent.mkdir(parents=True)
    robotws_case.write_text("*** Test Cases ***\nSmoke\n    No Operation\n", encoding="utf-8")
    (tmp_path / "testline_configuration" / "smoke").mkdir(parents=True)

    plan = build_robot_command_plan(
        {
            "testline": "smoke",
            "robotcase_path": "testsuite/smoke/login.robot",
            "uufSource": "some_legacy_uuf_path",
        },
        workspace_root=tmp_path,
    )

    assert plan["resolved_paths"]["output_dir"] == str((tmp_path / "artifacts" / "quicktest" / "retry-0" / "login").resolve())
    assert "some_legacy_uuf_path" not in plan["resolved_paths"]["output_dir"]
    assert plan["metadata"].get("legacy_uuf_source") is None
