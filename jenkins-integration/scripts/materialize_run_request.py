from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence
from urllib import request as urllib_request


def _clean_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _load_json_file(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _fetch_json(url: str, timeout_seconds: int = 30) -> dict[str, Any]:
    with urllib_request.urlopen(url, timeout=timeout_seconds) as response:
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


def materialize_robot_request(
    source_payload: dict[str, Any],
    *,
    workspace_root: Path | None = None,
    platform_api_base_url: str | None = None,
    python_env_template: str = "/home/ute/CIENV/{testline}",
) -> dict[str, Any]:
    payload = dict(source_payload)
    metadata = _normalize_mapping(payload.get("metadata"))

    executor_type = _clean_text(payload.get("executor_type")) or "robot"
    if executor_type != "robot":
        raise ValueError("Only robot executor_type can be materialized by this helper.")

    testline = _clean_text(payload.get("testline"))
    if testline is None:
        raise ValueError("testline is required.")

    robotcase_path = _clean_text(payload.get("robotcase_path"))
    if robotcase_path is None:
        raise ValueError("robotcase_path is required.")

    run_id = _clean_text(payload.get("run_id"))
    source_repos = _default_source_repo_specs(metadata)
    robotws_root = _resolve_path_text(
        _clean_text(_first_present(payload, "robotws_root", "robotPath")) or str(source_repos["robotws"].get("path") or "robotws"),
        workspace_root=workspace_root,
    )
    testline_config_root = _resolve_path_text(
        _clean_text(_first_present(payload, "testline_config_root", "testlineConfigRoot"))
        or str(source_repos["testline_configuration"].get("path") or "testline_configuration"),
        workspace_root=workspace_root,
    )

    request_payload = {
        "run_id": run_id,
        "executor_type": "robot",
        "testline": testline,
        "robotcase_path": robotcase_path,
        "build": _clean_text(payload.get("build")),
        "case_name": _clean_text(metadata.get("case_name") or payload.get("case_name")),
        "selected_tests": _normalize_sequence(metadata.get("selected_tests") or payload.get("selected_tests")),
        "variables": _normalize_mapping(metadata.get("robot_variables") or metadata.get("variables") or payload.get("variables")),
        "env_overrides": _normalize_mapping(metadata.get("env_overrides") or payload.get("env_overrides")),
        "artifact_label": _clean_text(metadata.get("artifact_label") or payload.get("artifact_label")) or "quicktest",
        "retry_index": metadata.get("retry_index") if metadata.get("retry_index") is not None else payload.get("retry_index", 0),
        "xunit_file": _clean_text(metadata.get("xunit_file") or payload.get("xunit_file")) or "quicktest.xml",
        "debug_file": _clean_text(metadata.get("debug_file") or payload.get("debug_file")) or "debug.log",
        "log_level": _clean_text(metadata.get("log_level") or payload.get("log_level")) or "TRACE",
        "python_env_root": _clean_text(metadata.get("python_env_root") or payload.get("python_env_root")) or python_env_template.format(testline=testline),
        "robotws_root": robotws_root,
        "testline_config_root": testline_config_root,
        "testline_variables_path": _resolve_path_text(
            _clean_text(metadata.get("testline_variables_path") or payload.get("testline_variables_path")),
            workspace_root=workspace_root,
        ),
        "source_repos": source_repos,
        "taf": {
            "mode": _clean_text(metadata.get("taf_mode")) or "reuse",
            "python_executable": _clean_text(metadata.get("taf_python_executable")) or "python3",
            "requirements_file": _clean_text(metadata.get("taf_requirements_file")),
            "package_specs": _normalize_sequence(metadata.get("taf_package_specs")),
        },
        "callback": {
            "base_url": _clean_text(platform_api_base_url) or _clean_text(metadata.get("platform_api_base_url")),
            "path": f"/api/runs/{run_id}/callbacks/jenkins" if run_id else None,
        },
        "public_contract_snapshot": {
            "run_id": run_id,
            "executor_type": executor_type,
            "testline": testline,
            "robotcase_path": robotcase_path,
            "build": _clean_text(payload.get("build")),
        },
    }
    return request_payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize a stable internal robot request from platform-api or ad-hoc input.")
    parser.add_argument("--input-json", type=Path, default=None, help="Optional JSON file containing a platform-api run detail or ad-hoc robot request.")
    parser.add_argument("--run-id", type=str, default=None, help="Optional run id fetched from platform-api when input-json is omitted.")
    parser.add_argument("--platform-api-base-url", type=str, default=None, help="Base URL used to fetch run detail and later callbacks.")
    parser.add_argument("--workspace-root", type=Path, default=None, help="Optional workspace root used to resolve relative internal paths.")
    parser.add_argument("--python-env-template", type=str, default="/home/ute/CIENV/{testline}", help="Default template for python_env_root when not provided.")
    parser.add_argument("--output-json", type=Path, required=True, help="Path to write the materialized internal request.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    payload = _load_json_file(args.input_json)
    if not payload:
        if not args.run_id or not args.platform_api_base_url:
            raise SystemExit("Either --input-json or both --run-id and --platform-api-base-url are required.")
        base_url = args.platform_api_base_url.rstrip("/")
        payload = _fetch_json(f"{base_url}/api/runs/{args.run_id}")

    request_payload = materialize_robot_request(
        payload,
        workspace_root=args.workspace_root.resolve() if args.workspace_root is not None else None,
        platform_api_base_url=args.platform_api_base_url,
        python_env_template=args.python_env_template,
    )
    output_text = json.dumps(request_payload, ensure_ascii=False, indent=2)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(output_text, encoding="utf-8")
    print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
