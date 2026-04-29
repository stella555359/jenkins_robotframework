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
    python_executable = _clean_text(taf_config.get("python_executable")) or "python3"
    mode = _clean_text(taf_config.get("mode")) or "reuse"
    requirements_file = _clean_text(taf_config.get("requirements_file"))
    package_specs = _normalize_sequence(taf_config.get("package_specs"))

    shell_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
    ]

    if mode == "create-venv":
        shell_lines.extend(
            [
                f"if [ ! -d {_quote(str(python_env_root))} ]; then",
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
        shell_lines.append("python -m pip install --upgrade pip")
        if requirements_file is not None:
            shell_lines.append(f"python -m pip install -r {_quote(requirements_file)}")
        for package_spec in package_specs:
            shell_lines.append(f"python -m pip install {_quote(package_spec)}")

    shell_script_text = "\n".join(shell_lines) + "\n"
    return {
        "testline": testline,
        "mode": mode,
        "python_env_root": str(python_env_root),
        "activate_script": str(activate_script),
        "python_executable": python_executable,
        "requirements_file": requirements_file,
        "package_specs": package_specs,
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
