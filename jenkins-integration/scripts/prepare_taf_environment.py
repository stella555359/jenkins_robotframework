from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
from typing import Any, Sequence


def _load_request(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _clean_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _normalize_sequence(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    raise ValueError("Expected a list of package specs.")


def _quote(path_text: str) -> str:
    return shlex.quote(path_text)


def build_taf_environment_plan(request_payload: dict[str, Any]) -> dict[str, Any]:
    taf_config = dict(request_payload.get("taf") or {})
    testline = _clean_text(request_payload.get("testline"))
    if testline is None:
        raise ValueError("testline is required.")

    python_env_root = Path(_clean_text(request_payload.get("python_env_root")) or f"/home/ute/CIENV/{testline}")
    activate_script = python_env_root / "bin" / "activate"
    robotws_root = Path(_clean_text(request_payload.get("robotws_root")) or "robotws")
    python_executable = _clean_text(taf_config.get("python_executable")) or "python3"
    mode = _clean_text(taf_config.get("mode")) or "reuse"
    requirements_file = _clean_text(taf_config.get("requirements_file"))
    package_specs = _normalize_sequence(taf_config.get("package_specs"))
    auto_install_from_robotws = mode == "create-venv" and not requirements_file and not package_specs

    shell_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
    ]

    if mode == "create-venv":
        shell_lines.extend(
            [
                f"if [ ! -f {_quote(str(activate_script))} ]; then",
                f"  mkdir -p {_quote(str(python_env_root.parent))}",
                f"  {python_executable} -m venv {_quote(str(python_env_root))}",
                "fi",
            ]
        )
    elif mode == "reuse":
        shell_lines.append(f"if [ ! -f {_quote(str(activate_script))} ]; then echo Missing activate script at {_quote(str(activate_script))}; exit 1; fi")
    elif mode == "skip-install":
        shell_lines.append("echo Skipping TAF environment installation by request")
    else:
        raise ValueError(f"Unsupported taf mode: {mode}")

    shell_lines.append(f". {_quote(str(activate_script))}")

    will_install = mode == "create-venv" or bool(requirements_file or package_specs)
    if will_install:
        shell_lines.extend(
            [
                'PIP_INDEX_URL_VALUE="${PIP_INDEX_URL_OVERRIDE:-${PIP_INDEX_URL:-}}"',
                'PIP_EXTRA_INDEX_URL_VALUE="${PIP_EXTRA_INDEX_URL_OVERRIDE:-${PIP_EXTRA_INDEX_URL:-}}"',
                'PIP_TRUSTED_HOST_VALUE="${PIP_TRUSTED_HOST_OVERRIDE:-${PIP_TRUSTED_HOST:-}}"',
                'PIP_INSTALL_INDEX_URL_VALUE="${PIP_INDEX_URL_VALUE:-$PIP_EXTRA_INDEX_URL_VALUE}"',
                'PIP_PROXY_VALUE="http://10.158.100.9:8080"',
            ]
        )
        if auto_install_from_robotws:
            shell_lines.extend(
                [
                    'if [ -z "$PIP_INSTALL_INDEX_URL_VALUE" ]; then echo "Missing internal pip index configuration. Set Jenkins global env PIP_INDEX_URL / PIP_EXTRA_INDEX_URL or job params PIP_INDEX_URL_OVERRIDE / PIP_EXTRA_INDEX_URL_OVERRIDE."; exit 1; fi',
                    'PIP_TRUSTED_HOST_ARGS=()',
                    'if [ -n "$PIP_TRUSTED_HOST_VALUE" ]; then',
                    '  for trusted_host in $PIP_TRUSTED_HOST_VALUE; do',
                    '    PIP_TRUSTED_HOST_ARGS+=(--trusted-host "$trusted_host")',
                    '  done',
                    'fi',
                ]
            )
        shell_lines.append("python -m pip install --upgrade pip")
        if requirements_file is not None:
            shell_lines.append(f"python -m pip install -r {_quote(requirements_file)}")
        elif auto_install_from_robotws:
            shell_lines.extend(
                [
                    f"ROBOTWS_ROOT={_quote(str(robotws_root))}",
                    "PYTHON_MM=$(python - <<'PY'",
                    "import sys",
                    "print(f\"{sys.version_info.major}{sys.version_info.minor}\")",
                    "PY",
                    ")",
                    'TAF_LOCK_FILE="$ROBOTWS_ROOT/dependencies.py${PYTHON_MM}-rf50.lock"',
                    'if [ -f "$TAF_LOCK_FILE" ]; then python -m pip install -r "$TAF_LOCK_FILE" --no-deps -i "$PIP_INSTALL_INDEX_URL_VALUE" --proxy "$PIP_PROXY_VALUE" "${PIP_TRUSTED_HOST_ARGS[@]}"; elif [ -f "$ROBOTWS_ROOT/requirements.cfg" ]; then python -m pip install -r "$ROBOTWS_ROOT/requirements.cfg" --no-deps -i "$PIP_INSTALL_INDEX_URL_VALUE" --proxy "$PIP_PROXY_VALUE" "${PIP_TRUSTED_HOST_ARGS[@]}"; else echo "Missing TAF dependency file under $ROBOTWS_ROOT. Expected $TAF_LOCK_FILE or requirements.cfg"; exit 1; fi',
                ]
            )
        for package_spec in package_specs:
            shell_lines.append(f"python -m pip install {_quote(package_spec)}")

    shell_script_text = "\n".join(shell_lines) + "\n"
    return {
        "testline": testline,
        "mode": mode,
        "python_env_root": str(python_env_root),
        "activate_script": str(activate_script),
        "robotws_root": str(robotws_root),
        "python_executable": python_executable,
        "requirements_file": requirements_file,
        "package_specs": package_specs,
        "auto_install_from_robotws": auto_install_from_robotws,
        "will_install": will_install,
        "shell_script_text": shell_script_text,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a TAF/python environment preparation plan.")
    parser.add_argument("--request-json", type=Path, required=True, help="Materialized internal request JSON.")
    parser.add_argument("--output-json", type=Path, required=True, help="Path to write the environment plan JSON.")
    parser.add_argument("--shell-script-output", type=Path, default=None, help="Optional path to write a shell script for environment preparation.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request_payload = _load_request(args.request_json)
    plan = build_taf_environment_plan(request_payload)
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
