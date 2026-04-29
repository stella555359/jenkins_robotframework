from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
from typing import Any, Sequence


REPO_CONVENTIONS = {
    "robotws": {
        "path": "robotws",
        "repo_url_env": "ROBOTWS_REPO_URL",
        "ref_env": "ROBOTWS_GIT_REF",
        "credentials_id_env": "ROBOTWS_CREDENTIALS_ID",
        "credential_kind": "sshagent",
    },
    "testline_configuration": {
        "path": "testline_configuration",
        "repo_url_env": "TESTLINE_CONFIGURATION_REPO_URL",
        "ref_env": "TESTLINE_CONFIGURATION_GIT_REF",
        "credentials_id_env": "TESTLINE_CONFIGURATION_CREDENTIALS_ID",
        "credential_kind": "sshagent",
    },
}


def _load_request(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _normalize_repo_spec(name: str, request_payload: dict[str, Any]) -> dict[str, Any]:
    source_repos = dict(request_payload.get("source_repos") or {})
    spec = dict(REPO_CONVENTIONS.get(name) or {})
    spec.update(dict(source_repos.get(name) or {}))
    spec["name"] = name
    return spec


def _quote(path_text: str) -> str:
    return shlex.quote(path_text)


def _append_effective_value_assignment(
    shell_lines: list[str],
    *,
    variable_name: str,
    env_name: str | None,
    explicit_value: str | None,
) -> None:
    if explicit_value is not None:
        default_variable_name = f"{variable_name}_DEFAULT"
        shell_lines.append(f"{default_variable_name}={_quote(explicit_value)}")
        if env_name is not None:
            shell_lines.append(f'{variable_name}="${{{env_name}:-${default_variable_name}}}"')
        else:
            shell_lines.append(f'{variable_name}="${default_variable_name}"')
        return

    if env_name is not None:
        shell_lines.append(f'{variable_name}="${{{env_name}:-}}"')
        return

    shell_lines.append(f'{variable_name}=""')


def build_checkout_plan(request_payload: dict[str, Any], *, workspace_root: Path) -> dict[str, Any]:
    repo_specs = [
        _normalize_repo_spec("robotws", request_payload),
        _normalize_repo_spec("testline_configuration", request_payload),
    ]

    operations: list[dict[str, Any]] = []
    shell_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {_quote(str(workspace_root.resolve()))}",
    ]

    for spec in repo_specs:
        relative_path = _clean_text(spec.get("path")) or spec["path"]
        repo_dir = (workspace_root / relative_path).resolve()
        repo_url = _clean_text(spec.get("repo_url"))
        ref = _clean_text(spec.get("ref"))
        repo_url_env = _clean_text(spec.get("repo_url_env"))
        ref_env = _clean_text(spec.get("ref_env"))
        credentials_id = _clean_text(spec.get("credentials_id"))
        credentials_id_env = _clean_text(spec.get("credentials_id_env"))
        credential_kind = _clean_text(spec.get("credential_kind")) or "sshagent"
        git_dir = repo_dir / ".git"
        env_prefix = spec["name"].upper()
        effective_repo_url_var = f"{env_prefix}_EFFECTIVE_REPO_URL"
        effective_ref_var = f"{env_prefix}_EFFECTIVE_REF"

        operation = {
            "name": spec["name"],
            "path": str(repo_dir),
            "repo_url": repo_url,
            "ref": ref,
            "repo_url_env": repo_url_env,
            "ref_env": ref_env,
            "credentials_id": credentials_id,
            "credentials_id_env": credentials_id_env,
            "credential_kind": credential_kind,
            "action": "reuse-existing" if repo_dir.exists() and not git_dir.exists() else "git-sync" if git_dir.exists() else "git-clone" if (repo_url or repo_url_env) else "missing-source",
        }

        _append_effective_value_assignment(
            shell_lines,
            variable_name=effective_repo_url_var,
            env_name=repo_url_env,
            explicit_value=repo_url,
        )
        _append_effective_value_assignment(
            shell_lines,
            variable_name=effective_ref_var,
            env_name=ref_env,
            explicit_value=ref,
        )

        if git_dir.exists():
            shell_lines.append(f'if [ -n "${{{effective_repo_url_var}}}" ]; then git -C {_quote(str(repo_dir))} remote set-url origin "${{{effective_repo_url_var}}}"; fi')
            shell_lines.append(f"git -C {_quote(str(repo_dir))} fetch --all --tags --prune")
            shell_lines.append(f'if [ -n "${{{effective_ref_var}}}" ]; then git -C {_quote(str(repo_dir))} checkout "${{{effective_ref_var}}}"; fi')
        elif repo_url is not None or repo_url_env is not None:
            shell_lines.append(f"mkdir -p {_quote(str(repo_dir.parent))}")
            shell_lines.append(f'if [ -z "${{{effective_repo_url_var}}}" ]; then echo Missing repo URL for {spec["name"]}. Set {repo_url_env or "an explicit repo_url"}.; exit 1; fi')
            shell_lines.append(f'if [ -n "${{{effective_ref_var}}}" ]; then git clone --branch "${{{effective_ref_var}}}" "${{{effective_repo_url_var}}}" {_quote(str(repo_dir))}; else git clone "${{{effective_repo_url_var}}}" {_quote(str(repo_dir))}; fi')
        elif repo_dir.exists():
            shell_lines.append(f"echo Reusing existing directory {_quote(str(repo_dir))} without git metadata")
        else:
            raise FileNotFoundError(
                f"Missing source for {spec['name']}: provide repo_url, set {repo_url_env}, or create an existing directory at {repo_dir}"
            )

        operations.append(operation)

    shell_script_text = "\n".join(shell_lines) + "\n"
    return {
        "workspace_root": str(workspace_root.resolve()),
        "operations": operations,
        "shell_script_text": shell_script_text,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a checkout plan for robotws and testline_configuration.")
    parser.add_argument("--request-json", type=Path, required=True, help="Materialized internal request JSON.")
    parser.add_argument("--workspace-root", type=Path, required=True, help="Workspace root containing repository checkouts.")
    parser.add_argument("--output-json", type=Path, required=True, help="Path to write the checkout plan JSON.")
    parser.add_argument("--shell-script-output", type=Path, default=None, help="Optional path to write a shell script for checkout execution.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request_payload = _load_request(args.request_json)
    plan = build_checkout_plan(request_payload, workspace_root=args.workspace_root)

    output_text = json.dumps(plan, ensure_ascii=False, indent=2)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(output_text, encoding="utf-8")

    if args.shell_script_output is not None:
        args.shell_script_output.parent.mkdir(parents=True, exist_ok=True)
        args.shell_script_output.write_text(plan["shell_script_text"], encoding="utf-8")

    print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
