import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(script_name: str):
    module_path = ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name.replace(".py", ""), module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


materialize_module = _load_module("materialize_run_request.py")
checkout_module = _load_module("checkout_sources.py")
taf_module = _load_module("prepare_taf_environment.py")
callback_module = _load_module("post_run_callback.py")


def test_materialize_robot_request_promotes_metadata_and_sources(tmp_path: Path) -> None:
    request_payload = materialize_module.materialize_robot_request(
        {
            "run_id": "run-20260429120000000",
            "executor_type": "robot",
            "testline": "7_5_UTE5G402T820",
            "robotcase_path": "testsuite/Hangzhou/RRM/example.robot",
            "build": "SBTS00_ENB_9999_260428_000008",
            "metadata": {
                "case_name": "Quick Smoke",
                "selected_tests": ["Quick Smoke", "Attach Smoke"],
                "robot_variables": {"AF_PATH": "http://example/release.zip"},
                "robotws_repo_url": "ssh://git/robotws.git",
                "robotws_ref": "master",
                "robotws_credentials_id": "robotws-ssh-key",
                "testline_configuration_repo_url": "ssh://git/testline_configuration.git",
                "testline_configuration_ref": "main",
                "testline_configuration_credentials_id": "testline-ssh-key",
                "taf_mode": "create-venv",
                "taf_package_specs": ["taf-core==1.0"],
            },
        },
        workspace_root=tmp_path,
        platform_api_base_url="http://127.0.0.1:8000",
    )

    assert request_payload["robotws_root"] == str((tmp_path / "robotws").resolve())
    assert request_payload["testline_config_root"] == str((tmp_path / "testline_configuration").resolve())
    assert request_payload["selected_tests"] == ["Quick Smoke", "Attach Smoke"]
    assert request_payload["variables"]["AF_PATH"] == "http://example/release.zip"
    assert request_payload["source_repos"]["robotws"]["repo_url"] == "ssh://git/robotws.git"
    assert request_payload["source_repos"]["robotws"]["credentials_id"] == "robotws-ssh-key"
    assert request_payload["source_repos"]["testline_configuration"]["credentials_id"] == "testline-ssh-key"
    assert request_payload["taf"]["mode"] == "create-venv"
    assert request_payload["callback"]["path"] == "/api/runs/run-20260429120000000/callbacks/jenkins"


def test_checkout_plan_builds_clone_commands_when_repo_urls_exist(tmp_path: Path) -> None:
    plan = checkout_module.build_checkout_plan(
        {
            "source_repos": {
                "robotws": {"path": "robotws", "repo_url": "ssh://git/robotws.git", "ref": "master", "credentials_id": "robotws-ssh-key"},
                "testline_configuration": {"path": "testline_configuration", "repo_url": "ssh://git/tl.git", "ref": "main"},
            }
        },
        workspace_root=tmp_path,
    )

    assert len(plan["operations"]) == 2
    assert plan["operations"][0]["credentials_id"] == "robotws-ssh-key"
    assert plan["operations"][0]["repo_url_env"] == "ROBOTWS_REPO_URL"
    assert 'ROBOTWS_EFFECTIVE_REPO_URL_DEFAULT=' in plan["shell_script_text"]
    assert 'git clone --branch "${ROBOTWS_EFFECTIVE_REF}" "${ROBOTWS_EFFECTIVE_REPO_URL}"' in plan["shell_script_text"]
    assert 'git clone --branch "${TESTLINE_CONFIGURATION_EFFECTIVE_REF}" "${TESTLINE_CONFIGURATION_EFFECTIVE_REPO_URL}"' in plan["shell_script_text"]


def test_prepare_taf_environment_plan_supports_create_venv_install_mode() -> None:
    plan = taf_module.build_taf_environment_plan(
        {
            "testline": "7_5_UTE5G402T820",
            "python_env_root": "/home/ute/CIENV/7_5_UTE5G402T820",
            "taf": {
                "mode": "create-venv",
                "python_executable": "python3.11",
                "requirements_file": "deploy/env/requirements-robot.txt",
                "package_specs": ["taf-core==1.0", "taf-rf==2.0"],
            },
        }
    )

    assert plan["mode"] == "create-venv"
    assert plan["will_install"] is True
    assert "python3.11 -m venv '/home/ute/CIENV/7_5_UTE5G402T820'" in plan["shell_script_text"]
    assert "python -m pip install -r deploy/env/requirements-robot.txt" in plan["shell_script_text"]
    assert "python -m pip install taf-core==1.0" in plan["shell_script_text"]


def test_post_run_callback_collects_artifacts_and_builds_payload(tmp_path: Path) -> None:
    output_xml = tmp_path / "artifact" / "quicktest" / "output.xml"
    output_xml.parent.mkdir(parents=True)
    output_xml.write_text("<robot />\n", encoding="utf-8")

    manifest = callback_module.collect_artifact_manifest(artifact_dir=tmp_path / "artifact")
    payload = callback_module.build_callback_payload(
        status="passed",
        message="Robot execution completed.",
        jenkins_build_ref="robot-execution#15",
        artifact_manifest=manifest,
        metadata={"testline": "7_5_UTE5G402T820"},
    )

    assert manifest[0]["label"] == "output.xml"
    assert payload["status"] == "passed"
    assert payload["artifact_manifest"][0]["path"] == str(output_xml.resolve())
    assert payload["metadata"]["testline"] == "7_5_UTE5G402T820"


def test_post_run_callback_retries_and_writes_fallback(tmp_path: Path) -> None:
    fallback_output = tmp_path / "callback-fallback.json"

    def failing_sender(**_: object) -> dict[str, object]:
        raise OSError("platform temporarily unavailable")

    send_result = callback_module.send_callback_with_retry(
        base_url="http://127.0.0.1:8000",
        run_id="run-20260429123000000",
        payload={"status": "failed"},
        max_attempts=3,
        backoff_seconds=0.01,
        fallback_output_json=fallback_output,
        ignore_send_failure=True,
        send_operation=failing_sender,
        sleep_operation=lambda _: None,
    )

    fallback_payload = json.loads(fallback_output.read_text(encoding="utf-8"))
    assert send_result["sent"] is False
    assert send_result["attempt_count"] == 3
    assert len(send_result["attempts"]) == 3
    assert fallback_payload["callback_url"].endswith("/api/runs/run-20260429123000000/callbacks/jenkins")
    assert fallback_payload["payload"]["status"] == "failed"
