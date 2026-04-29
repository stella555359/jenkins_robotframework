from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
from typing import Any, Sequence


def _clean_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def _load_payload(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_path(path_text: str | Path | None, *, base_dir: Path) -> Path | None:
    if path_text is None:
        return None
    path = Path(str(path_text))
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _require_text(field_name: str, value: Any) -> str:
    cleaned = _clean_text(value)
    if cleaned is None:
        raise ValueError(f"{field_name} is required.")
    return cleaned


def _parse_bool(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean value: {value}")


def _parse_int(value: Any, *, default: int = 0) -> int:
    if value is None or str(value).strip() == "":
        return default
    return int(str(value).strip())


def _parse_mapping_value(raw_value: Any) -> dict[str, str]:
    if raw_value is None:
        return {}
    if isinstance(raw_value, dict):
        return {str(key): str(value) for key, value in raw_value.items()}
    raise ValueError("Expected a mapping for robot variables or environment overrides.")


def _parse_sequence_value(raw_value: Any) -> list[str]:
    if raw_value is None:
        return []
    if isinstance(raw_value, (list, tuple)):
        return [str(item).strip() for item in raw_value if str(item).strip()]
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return []
    return [line.strip() for line in cleaned.splitlines() if line.strip()]


def _parse_cli_variables(entries: Sequence[str]) -> dict[str, str]:
    variables: dict[str, str] = {}
    for entry in entries:
        if "=" not in entry:
            raise ValueError(f"Invalid robot variable '{entry}'. Use KEY=VALUE.")
        key, value = entry.split("=", 1)
        key = _require_text("robot variable key", key)
        variables[key] = value
    return variables


def _parse_legacy_pkg_path(raw_value: str | None) -> dict[str, str]:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return {}

    tokens = shlex.split(cleaned)
    if not tokens:
        return {}

    parsed_variables: dict[str, str] = {}
    index = 0
    first_token = tokens[0]
    if not first_token.startswith("-"):
        parsed_variables["AF_PATH"] = first_token
        index = 1

    while index < len(tokens):
        token = tokens[index]
        if token == "-v" and index + 1 < len(tokens):
            assignment = tokens[index + 1]
            if ":" in assignment:
                key, value = assignment.split(":", 1)
                parsed_variables[_require_text("robot variable key", key)] = value
            index += 2
            continue
        index += 1

    return parsed_variables


def _parse_legacy_robot_suites(raw_value: str | None) -> tuple[list[str], str | None]:
    cleaned = _clean_text(raw_value)
    if cleaned is None:
        return [], None

    tokens = shlex.split(cleaned)
    selected_tests: list[str] = []
    robotcase_path: str | None = None
    index = 0

    while index < len(tokens):
        token = tokens[index]
        if token == "-t" and index + 1 < len(tokens):
            selected_tests.append(tokens[index + 1])
            index += 2
            continue
        if not token.startswith("-"):
            robotcase_path = token
        index += 1

    return selected_tests, robotcase_path


def _merge_selected_tests(*sources: Sequence[str]) -> list[str]:
    merged: list[str] = []
    for source in sources:
        for item in source:
            if item not in merged:
                merged.append(item)
    return merged


def _shell_quote_command(command: Sequence[str]) -> str:
    return shlex.join(list(command))


def _default_output_dir(
    *,
    workspace_root: Path,
    artifact_root_dir: Path | None,
    artifact_label: str,
    retry_index: int,
    resolved_robot_case_path: Path,
) -> Path:
    base_dir = (artifact_root_dir or (workspace_root / "artifacts")).resolve()
    return (base_dir / artifact_label / f"retry-{retry_index}" / resolved_robot_case_path.stem).resolve()


def _resolve_robot_case_path(
    robotcase_path: str,
    *,
    workspace_root: Path,
    robotws_root: Path,
    allow_missing_paths: bool,
) -> Path:
    candidate = Path(robotcase_path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
        if allow_missing_paths or resolved.exists():
            return resolved
        raise FileNotFoundError(f"robot case path not found: {resolved}")

    direct_path = (workspace_root / candidate).resolve()
    if direct_path.exists():
        return direct_path

    robotws_relative_path = (robotws_root / candidate).resolve()
    if robotws_relative_path.exists() or allow_missing_paths:
        return robotws_relative_path

    raise FileNotFoundError(
        "robot case path not found under workspace root or robotws root: "
        f"{direct_path} | {robotws_relative_path}"
    )


def _resolve_testline_variables_path(
    testline: str,
    *,
    workspace_root: Path,
    testline_config_root: Path,
    explicit_path: Path | None,
    allow_missing_paths: bool,
) -> Path:
    resolved = explicit_path or (testline_config_root / testline).resolve()
    if allow_missing_paths or resolved.exists():
        return resolved
    raise FileNotFoundError(f"testline variables path not found: {resolved}")


def build_robot_command_plan(
    payload: dict[str, Any],
    *,
    workspace_root: Path,
    python_executable: str = "python",
    robotws_root: Path | None = None,
    testline_config_root: Path | None = None,
    python_env_root: Path | None = None,
    output_dir: Path | None = None,
    artifact_root_dir: Path | None = None,
    artifact_label: str | None = None,
    retry_index: int | None = None,
    xunit_file: str | None = None,
    debug_file: str | None = None,
    log_level: str | None = None,
    case_name: str | None = None,
    selected_tests: Sequence[str] | None = None,
    testline_variables_path: Path | None = None,
    variables: dict[str, str] | None = None,
    env_overrides: dict[str, str] | None = None,
    extra_robot_args: Sequence[str] | None = None,
    clear_proxy_env: bool | None = None,
    dryrun_mode: bool | None = None,
    allow_missing_paths: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    workspace_root = workspace_root.resolve()
    resolved_robotws_root = (
        robotws_root
        or _resolve_path(_first_present(payload, "robotws_root", "robotPath"), base_dir=workspace_root)
        or (workspace_root / "robotws")
    ).resolve()
    resolved_testline_config_root = (
        testline_config_root
        or _resolve_path(_first_present(payload, "testline_config_root", "testlineConfigRoot"), base_dir=workspace_root)
        or (workspace_root / "testline_configuration")
    ).resolve()
    resolved_python_env_root = (
        python_env_root
        or _resolve_path(_first_present(payload, "python_env_root", "pythonPath"), base_dir=workspace_root)
    )

    resolved_run_id = _clean_text(run_id or payload.get("run_id"))
    testline = _require_text("testline", payload.get("testline"))
    resolved_case_name = _clean_text(case_name or _first_present(payload, "case_name", "caseName"))

    legacy_selected_tests, legacy_robotcase_path = _parse_legacy_robot_suites(
        _first_present(payload, "robot_suites", "robotSuites")
    )
    robotcase_path = _require_text(
        "robotcase_path",
        payload.get("robotcase_path") or legacy_robotcase_path,
    )

    resolved_selected_tests = _merge_selected_tests(
        _parse_sequence_value(_first_present(payload, "selected_tests", "selectedTests")),
        list(selected_tests or []),
        legacy_selected_tests,
        [resolved_case_name] if resolved_case_name else [],
    )

    resolved_retry_index = retry_index
    if resolved_retry_index is None:
        resolved_retry_index = _parse_int(
            _first_present(payload, "retry_index", "retryIndex", "retry_times", "retryTimes"),
            default=0,
        )

    resolved_artifact_label = _clean_text(
        artifact_label or _first_present(payload, "artifact_label", "artifactLabel")
    ) or "quicktest"
    resolved_xunit_file = _clean_text(xunit_file or _first_present(payload, "xunit_file", "xunitFile")) or "quicktest.xml"
    resolved_debug_file = _clean_text(debug_file or _first_present(payload, "debug_file", "debugFile")) or "debug.log"
    resolved_log_level = _clean_text(log_level or _first_present(payload, "log_level", "logLevel")) or "TRACE"
    resolved_dryrun_mode = dryrun_mode
    if resolved_dryrun_mode is None:
        resolved_dryrun_mode = _parse_bool(_first_present(payload, "dryrun_mode", "dryrunMode"), default=False)

    payload_output_dir = _resolve_path(_first_present(payload, "output_dir", "outputDir"), base_dir=workspace_root)
    payload_artifact_root_dir = _resolve_path(
        _first_present(payload, "artifact_root_dir", "artifactRootDir"),
        base_dir=workspace_root,
    )

    payload_variables_path = _resolve_path(
        _first_present(payload, "testline_variables_path", "testlineVariablesPath", "configPath"),
        base_dir=workspace_root,
    )
    explicit_variables_path = testline_variables_path or payload_variables_path
    resolved_variables_path = _resolve_testline_variables_path(
        testline,
        workspace_root=workspace_root,
        testline_config_root=resolved_testline_config_root,
        explicit_path=explicit_variables_path,
        allow_missing_paths=allow_missing_paths,
    )

    resolved_robot_case_path = _resolve_robot_case_path(
        robotcase_path,
        workspace_root=workspace_root,
        robotws_root=resolved_robotws_root,
        allow_missing_paths=allow_missing_paths,
    )

    resolved_output_dir = (
        output_dir
        or payload_output_dir
        or _default_output_dir(
            workspace_root=workspace_root,
            artifact_root_dir=artifact_root_dir or payload_artifact_root_dir,
            artifact_label=resolved_artifact_label,
            retry_index=resolved_retry_index,
            resolved_robot_case_path=resolved_robot_case_path,
        )
    ).resolve()

    merged_variables = _parse_mapping_value(_first_present(payload, "variables", "robot_variables", "robotVariables"))
    merged_variables.update(_parse_legacy_pkg_path(_first_present(payload, "pkg_path", "pkgPath")))
    merged_variables.update(variables or {})

    clear_proxy_by_default = clear_proxy_env
    if clear_proxy_by_default is None:
        clear_proxy_by_default = _parse_bool(
            _first_present(payload, "clear_proxy_env", "clearProxyEnv"),
            default=True,
        )
    merged_env_overrides: dict[str, str] = {}
    if clear_proxy_by_default:
        merged_env_overrides.update({"http_proxy": "", "https_proxy": ""})
    merged_env_overrides.update(_parse_mapping_value(_first_present(payload, "env_overrides", "envOverrides")))
    merged_env_overrides.update(env_overrides or {})

    merged_extra_robot_args = [str(value) for value in list(payload.get("extra_robot_args") or [])]
    merged_extra_robot_args.extend(str(value) for value in list(extra_robot_args or []))

    command = [
        python_executable,
        "-m",
        "robot",
        "--pythonpath",
        str(resolved_robotws_root),
    ]

    ordered_variable_keys = [key for key in ["AF_PATH"] if key in merged_variables]
    ordered_variable_keys.extend(sorted(key for key in merged_variables if key not in {"AF_PATH"}))
    for key in ordered_variable_keys:
        command.extend(["-v", f"{key}:{merged_variables[key]}"])

    command.extend(["-x", resolved_xunit_file])
    command.extend(["-b", resolved_debug_file])
    command.extend(["-d", str(resolved_output_dir)])
    command.extend(["-V", str(resolved_variables_path)])
    command.extend(["-L", resolved_log_level])

    if resolved_dryrun_mode:
        command.append("--dryrun")

    for test_name in resolved_selected_tests:
        command.extend(["-t", test_name])

    command.extend(merged_extra_robot_args)
    command.append(str(resolved_robot_case_path))

    activate_script = resolved_python_env_root / "bin" / "activate" if resolved_python_env_root is not None else None
    shell_lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        f"cd {shlex.quote(str(workspace_root))}",
    ]
    if activate_script is not None:
        shell_lines.append(f". {shlex.quote(str(activate_script))}")
    for key, value in merged_env_overrides.items():
        shell_lines.append(f"export {key}={shlex.quote(value)}")
    shell_lines.append(_shell_quote_command(command))
    shell_script_text = "\n".join(shell_lines) + "\n"

    return {
        "executor_type": "robot",
        "run_id": resolved_run_id,
        "testline": testline,
        "robotcase_path": robotcase_path,
        "command": command,
        "command_text": _shell_quote_command(command),
        "resolved_paths": {
            "workspace_root": str(workspace_root),
            "robotws_root": str(resolved_robotws_root),
            "testline_config_root": str(resolved_testline_config_root),
            "testline_variables_path": str(resolved_variables_path),
            "robot_case_path": str(resolved_robot_case_path),
            "output_dir": str(resolved_output_dir),
            "python_env_root": str(resolved_python_env_root) if resolved_python_env_root is not None else None,
            "activate_script": str(activate_script) if activate_script is not None else None,
        },
        "execution": {
            "dryrun_mode": resolved_dryrun_mode,
            "retry_index": resolved_retry_index,
            "artifact_label": resolved_artifact_label,
            "selected_tests": resolved_selected_tests,
            "xunit_file": resolved_xunit_file,
            "debug_file": resolved_debug_file,
            "log_level": resolved_log_level,
        },
        "shell": {
            "env_overrides": merged_env_overrides,
            "shell_script_text": shell_script_text,
        },
        "metadata": {
            "case_name": resolved_case_name,
            "variables": merged_variables,
            "extra_robot_args": merged_extra_robot_args,
            "legacy_pkg_path": _clean_text(_first_present(payload, "pkg_path", "pkgPath")),
            "legacy_robot_suites": _clean_text(_first_present(payload, "robot_suites", "robotSuites")),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a Robot Framework command plan for Jenkins execution.")
    parser.add_argument("--request-json", type=Path, default=None, help="Optional JSON payload containing run metadata.")
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd(), help="Workspace root containing robotws and testline_configuration.")
    parser.add_argument("--robotws-root", type=Path, default=None, help="Optional explicit robotws root path.")
    parser.add_argument("--testline-config-root", type=Path, default=None, help="Optional explicit testline_configuration root path.")
    parser.add_argument("--python-env-root", type=Path, default=None, help="Optional Python virtual environment root used to resolve bin/activate.")
    parser.add_argument("--testline", type=str, default=None, help="Target testline name.")
    parser.add_argument("--robotcase-path", type=str, default=None, help="Robot case path, relative to workspace or robotws.")
    parser.add_argument("--case-name", type=str, default=None, help="Optional Robot test case name passed with -t.")
    parser.add_argument("--selected-test", action="append", default=[], help="Robot test case name passed with repeated -t options.")
    parser.add_argument("--testline-variables-path", type=Path, default=None, help="Optional explicit Robot variable file path.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Artifact output directory passed with -d.")
    parser.add_argument("--artifact-root-dir", type=Path, default=None, help="Optional artifact root used to build the default output directory.")
    parser.add_argument("--artifact-label", type=str, default=None, help="Artifact label segment used in default output directory naming.")
    parser.add_argument("--retry-index", type=int, default=None, help="Retry index used in default output directory naming.")
    parser.add_argument("--xunit-file", type=str, default=None, help="Robot xUnit output file name passed with -x.")
    parser.add_argument("--debug-file", type=str, default=None, help="Robot debug log file name passed with -b.")
    parser.add_argument("--log-level", type=str, default=None, help="Robot log level passed with -L.")
    parser.add_argument("--run-id", type=str, default=None, help="Optional run id used for default artifact directory naming.")
    parser.add_argument("--python-executable", type=str, default="python", help="Python executable used to invoke Robot Framework.")
    parser.add_argument("--variable", action="append", default=[], help="Robot variable in KEY=VALUE format. Can be repeated.")
    parser.add_argument("--env-override", action="append", default=[], help="Shell environment override in KEY=VALUE format. Can be repeated.")
    parser.add_argument("--extra-robot-arg", action="append", default=[], help="Additional raw argument passed to python -m robot.")
    parser.add_argument("--dryrun", action="store_true", help="Append --dryrun to the Robot command.")
    parser.add_argument("--keep-proxy-env", action="store_true", help="Do not automatically blank http_proxy and https_proxy in the shell plan.")
    parser.add_argument("--allow-missing-paths", action="store_true", help="Do not fail if case path or variable path does not exist yet.")
    parser.add_argument("--output-json", type=Path, default=None, help="Optional file path to persist the generated command plan.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = _load_payload(args.request_json)

    if args.testline is not None:
        payload["testline"] = args.testline
    if args.robotcase_path is not None:
        payload["robotcase_path"] = args.robotcase_path
    if args.case_name is not None:
        payload["case_name"] = args.case_name
    if args.testline_variables_path is not None:
        payload["testline_variables_path"] = str(args.testline_variables_path)
    if args.output_dir is not None:
        payload["output_dir"] = str(args.output_dir)
    if args.python_env_root is not None:
        payload["python_env_root"] = str(args.python_env_root)
    if args.selected_test:
        payload["selected_tests"] = list(args.selected_test)
    if args.artifact_root_dir is not None:
        payload["artifact_root_dir"] = str(args.artifact_root_dir)
    if args.artifact_label is not None:
        payload["artifact_label"] = args.artifact_label
    if args.retry_index is not None:
        payload["retry_index"] = args.retry_index
    if args.xunit_file is not None:
        payload["xunit_file"] = args.xunit_file
    if args.debug_file is not None:
        payload["debug_file"] = args.debug_file
    if args.log_level is not None:
        payload["log_level"] = args.log_level
    if args.run_id is not None:
        payload["run_id"] = args.run_id
    if args.dryrun:
        payload["dryrun_mode"] = True

    plan = build_robot_command_plan(
        payload,
        workspace_root=args.workspace_root,
        python_executable=args.python_executable,
        robotws_root=args.robotws_root,
        testline_config_root=args.testline_config_root,
        python_env_root=args.python_env_root,
        output_dir=args.output_dir,
        artifact_root_dir=args.artifact_root_dir,
        artifact_label=args.artifact_label,
        retry_index=args.retry_index,
        xunit_file=args.xunit_file,
        debug_file=args.debug_file,
        log_level=args.log_level,
        case_name=args.case_name,
        selected_tests=args.selected_test,
        testline_variables_path=args.testline_variables_path,
        variables=_parse_cli_variables(args.variable),
        env_overrides=_parse_cli_variables(args.env_override),
        extra_robot_args=args.extra_robot_arg,
        clear_proxy_env=not args.keep_proxy_env,
        dryrun_mode=args.dryrun,
        allow_missing_paths=args.allow_missing_paths,
        run_id=args.run_id,
    )

    output_text = json.dumps(plan, ensure_ascii=False, indent=2)
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(output_text, encoding="utf-8")
    print(output_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
