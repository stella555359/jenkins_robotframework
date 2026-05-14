from __future__ import annotations

import argparse
import json
from pathlib import Path
import ssl
from typing import Any, Sequence
from urllib import request as urllib_request


def _clean_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _load_json_file(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _loads_json_object(raw_value: str | None, *, field_name: str) -> dict[str, Any]:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return {}
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError(f"{field_name} must be a JSON object.")
    return dict(payload)


def _fetch_json(url: str, timeout_seconds: int = 30, verify_tls: bool = True) -> dict[str, Any]:
    ssl_context = None if verify_tls else ssl._create_unverified_context()
    with urllib_request.urlopen(url, timeout=timeout_seconds, context=ssl_context) as response:
        return json.loads(response.read().decode("utf-8"))


def _normalize_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    return dict(value)


def _normalize_sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    raise ValueError("Expected a JSON array.")


def _resolve_path_text(path_text: str | None, *, workspace_root: Path | None) -> str | None:
    cleaned = _clean_text(path_text)
    if cleaned is None:
        return None
    path = Path(cleaned)
    if path.is_absolute() or workspace_root is None:
        return str(path)
    return str((workspace_root / path).resolve())


def _default_source_repo_specs(metadata: dict[str, Any]) -> dict[str, Any]:
    source_repos = _normalize_mapping(metadata.get("source_repos"))
    robotws_spec = _normalize_mapping(source_repos.get("robotws"))
    testline_spec = _normalize_mapping(source_repos.get("testline_configuration"))

    robotws_spec.setdefault("path", metadata.get("robotws_path") or "robotws")
    testline_spec.setdefault("path", metadata.get("testline_configuration_path") or "testline_configuration")

    robotws_repo_url = _clean_text(metadata.get("robotws_repo_url"))
    if robotws_repo_url is not None:
        robotws_spec.setdefault("repo_url", robotws_repo_url)
    robotws_ref = _clean_text(metadata.get("robotws_ref") or metadata.get("robotws_branch"))
    if robotws_ref is not None:
        robotws_spec.setdefault("ref", robotws_ref)
    robotws_credentials_id = _clean_text(metadata.get("robotws_credentials_id"))
    if robotws_credentials_id is not None:
        robotws_spec.setdefault("credentials_id", robotws_credentials_id)
    robotws_credential_kind = _clean_text(metadata.get("robotws_credential_kind"))
    if robotws_credential_kind is not None:
        robotws_spec.setdefault("credential_kind", robotws_credential_kind)

    testline_repo_url = _clean_text(metadata.get("testline_configuration_repo_url"))
    if testline_repo_url is not None:
        testline_spec.setdefault("repo_url", testline_repo_url)
    testline_ref = _clean_text(metadata.get("testline_configuration_ref") or metadata.get("testline_configuration_branch"))
    if testline_ref is not None:
        testline_spec.setdefault("ref", testline_ref)
    testline_credentials_id = _clean_text(metadata.get("testline_configuration_credentials_id"))
    if testline_credentials_id is not None:
        testline_spec.setdefault("credentials_id", testline_credentials_id)
    testline_credential_kind = _clean_text(metadata.get("testline_configuration_credential_kind"))
    if testline_credential_kind is not None:
        testline_spec.setdefault("credential_kind", testline_credential_kind)

    return {
        "robotws": robotws_spec,
        "testline_configuration": testline_spec,
    }


def _find_runner_request(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = _normalize_mapping(payload.get("metadata"))
    runner_request = metadata.get("runner_request")
    if isinstance(runner_request, dict):
        return dict(runner_request)
    if "traffic_plan" in payload:
        return dict(payload)
    return {}


def _workflow_spec_from_payload(payload: dict[str, Any], fallback_workflow_spec: dict[str, Any]) -> dict[str, Any]:
    workflow_spec = payload.get("workflow_spec")
    if isinstance(workflow_spec, dict):
        return dict(workflow_spec)
    return dict(fallback_workflow_spec)


def _selected_ues_from_payload(payload: dict[str, Any]) -> list[Any]:
    metadata = _normalize_mapping(payload.get("metadata"))
    selected_ues = metadata.get("selected_ues")
    if isinstance(selected_ues, list):
        return list(selected_ues)
    return []


def _apply_build_to_kpi_generator_items(request_payload: dict[str, Any], build: str | None) -> None:
    if build is None:
        return
    traffic_plan = _normalize_mapping(request_payload.get("traffic_plan"))
    for stage in _normalize_sequence(traffic_plan.get("stages")):
        if not isinstance(stage, dict):
            continue
        for item in _normalize_sequence(stage.get("items")):
            if not isinstance(item, dict) or item.get("model") != "kpi_generator":
                continue
            params = _normalize_mapping(item.get("params"))
            params.setdefault("build", build)
            item["params"] = params


def materialize_python_orchestrator_request(
    source_payload: dict[str, Any],
    *,
    workflow_spec: dict[str, Any],
    testline: str | None,
    workflow_name: str | None,
    build: str | None,
    dry_run: bool | None,
    workspace_root: Path | None = None,
    python_env_template: str = "/home/ute/CIENV/{testline}",
    python_env_root: str | None = None,
    taf_mode: str | None = None,
    robotws_root: str | None = None,
    testline_variables_path: str | None = None,
    runner_repository_root: str | None = None,
    result_json_path: str | None = None,
    artifact_label: str | None = None,
    retry_index: str | None = None,
) -> dict[str, Any]:
    payload = dict(source_payload)
    metadata = _normalize_mapping(payload.get("metadata"))
    runner_request = _find_runner_request(payload)
    workflow_spec = _workflow_spec_from_payload(payload, workflow_spec)

    effective_testline = _clean_text(testline) or _clean_text(payload.get("testline")) or _clean_text(runner_request.get("testline"))
    if effective_testline is None:
        raise ValueError("testline is required.")

    effective_workflow_name = _clean_text(workflow_name) or _clean_text(payload.get("workflow_name")) or _clean_text(workflow_spec.get("name"))
    effective_build = _clean_text(build) or _clean_text(payload.get("build")) or _clean_text(runner_request.get("build"))

    if not runner_request:
        runner_request = {
            "testline": effective_testline,
            "ue_selection": {
                "selected_ues": _selected_ues_from_payload(payload),
            },
            "traffic_plan": {
                "stages": _normalize_sequence(workflow_spec.get("stages")),
            },
            "runtime_options": _normalize_mapping(workflow_spec.get("runtime_options")),
        }

    runner_request["run_id"] = _clean_text(payload.get("run_id"))
    runner_request["executor_type"] = "python_orchestrator"
    runner_request["testline"] = effective_testline
    runner_request["workflow_name"] = effective_workflow_name
    runner_request["build"] = effective_build
    runner_request["workflow_spec"] = workflow_spec
    runner_request["source_repos"] = _default_source_repo_specs(metadata)
    runner_request["robotws_root"] = _resolve_path_text(
        _clean_text(robotws_root) or _clean_text(metadata.get("robotws_root")) or str(runner_request["source_repos"]["robotws"].get("path") or "robotws"),
        workspace_root=workspace_root,
    )
    runner_request["testline_variables_path"] = _resolve_path_text(
        _clean_text(testline_variables_path) or _clean_text(metadata.get("testline_variables_path")),
        workspace_root=workspace_root,
    )
    runner_request["runner_repository_root"] = _resolve_path_text(
        _clean_text(runner_repository_root) or _clean_text(metadata.get("runner_repository_root")) or "test-workflow-runner",
        workspace_root=workspace_root,
    )
    runner_request["result_json_path"] = _resolve_path_text(
        _clean_text(result_json_path) or _clean_text(metadata.get("result_json_path")) or "artifacts/python-kpi-runner-result.json",
        workspace_root=workspace_root,
    )
    runner_request["artifact_label"] = _clean_text(artifact_label) or _clean_text(metadata.get("artifact_label")) or "kpi-runner"
    runner_request["retry_index"] = _clean_text(retry_index) or _clean_text(metadata.get("retry_index")) or "0"

    runtime_options = _normalize_mapping(runner_request.get("runtime_options"))
    if dry_run is not None:
        runtime_options["dry_run"] = dry_run
    runner_request["runtime_options"] = runtime_options

    taf = _normalize_mapping(runner_request.get("taf"))
    taf["mode"] = _clean_text(taf_mode) or _clean_text(metadata.get("taf_mode")) or _clean_text(taf.get("mode")) or "reuse"
    taf.setdefault("python_executable", _clean_text(metadata.get("taf_python_executable")) or "python3")
    taf.setdefault("requirements_file", _clean_text(metadata.get("taf_requirements_file")))
    taf.setdefault("package_specs", _normalize_sequence(metadata.get("taf_package_specs")))
    runner_request["taf"] = taf

    runner_request["python_env_root"] = (
        _clean_text(python_env_root)
        or _clean_text(metadata.get("python_env_root"))
        or _clean_text(runner_request.get("python_env_root"))
        or python_env_template.format(testline=effective_testline)
    )
    runner_request["public_contract_snapshot"] = {
        "run_id": runner_request.get("run_id"),
        "executor_type": "python_orchestrator",
        "testline": effective_testline,
        "workflow_name": effective_workflow_name,
        "build": effective_build,
        "dry_run": runtime_options.get("dry_run"),
    }

    _apply_build_to_kpi_generator_items(runner_request, effective_build)
    return runner_request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize a test-workflow-runner request from platform-api python_orchestrator data.")
    parser.add_argument("--input-json", type=Path, default=None, help="Optional JSON file containing a platform-api run detail or runner request.")
    parser.add_argument("--run-id", type=str, default=None, help="Optional run id fetched from platform-api when input-json is omitted.")
    parser.add_argument("--platform-api-base-url", type=str, default=None, help="Base URL used to fetch run detail.")
    parser.add_argument("--insecure-skip-tls-verify", action="store_true", help="Skip TLS certificate verification when fetching run detail from platform-api.")
    parser.add_argument("--workflow-spec-json", type=str, default=None, help="WorkflowSpec JSON passed directly by Jenkins parameter.")
    parser.add_argument("--testline", type=str, default=None, help="Target testline.")
    parser.add_argument("--workflow-name", type=str, default=None, help="Human-readable workflow name.")
    parser.add_argument("--build", type=str, default=None, help="CIT package / software build under test.")
    parser.add_argument("--dry-run", action="store_true", help="Force runtime_options.dry_run=true.")
    parser.add_argument("--workspace-root", type=Path, default=None, help="Optional workspace root used to resolve relative paths.")
    parser.add_argument("--python-env-template", type=str, default="/home/ute/CIENV/{testline}", help="Default template for python_env_root when not provided.")
    parser.add_argument("--python-env-root", type=str, default=None, help="Optional explicit Python environment root.")
    parser.add_argument("--taf-mode", type=str, default=None, help="TAF/python environment mode.")
    parser.add_argument("--robotws-root", type=str, default=None, help="Optional robotws root path.")
    parser.add_argument("--testline-variables-path", type=str, default=None, help="Optional explicit testline variables path.")
    parser.add_argument("--runner-repository-root", type=str, default=None, help="Optional test-workflow-runner repository root.")
    parser.add_argument("--result-json-path", type=str, default=None, help="Optional runner result JSON path.")
    parser.add_argument("--artifact-label", type=str, default=None, help="Artifact label segment.")
    parser.add_argument("--retry-index", type=str, default=None, help="Retry index.")
    parser.add_argument("--output-json", type=Path, required=True, help="Path to write the materialized runner request.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = _load_json_file(args.input_json)
    if not payload and args.run_id and args.platform_api_base_url:
        base_url = args.platform_api_base_url.rstrip("/")
        payload = _fetch_json(
            f"{base_url}/api/runs/{args.run_id}",
            verify_tls=not args.insecure_skip_tls_verify,
        )

    workflow_spec = _loads_json_object(args.workflow_spec_json, field_name="workflow_spec_json")
    request_payload = materialize_python_orchestrator_request(
        payload,
        workflow_spec=workflow_spec,
        testline=args.testline,
        workflow_name=args.workflow_name,
        build=args.build,
        dry_run=True if args.dry_run else None,
        workspace_root=args.workspace_root.resolve() if args.workspace_root is not None else None,
        python_env_template=args.python_env_template,
        python_env_root=args.python_env_root,
        taf_mode=args.taf_mode,
        robotws_root=args.robotws_root,
        testline_variables_path=args.testline_variables_path,
        runner_repository_root=args.runner_repository_root,
        result_json_path=args.result_json_path,
        artifact_label=args.artifact_label,
        retry_index=args.retry_index,
    )
    output_text = json.dumps(request_payload, ensure_ascii=False, indent=2)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(output_text, encoding="utf-8")
    print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
