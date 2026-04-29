from __future__ import annotations

import argparse
from pathlib import Path
from types import SimpleNamespace
from typing import Sequence

from .config_resolver import EnvConfigResolver
from .models import KpiTestModelRequest, NormalizedUe, OrchestratorState, TestlineContext
from .request_loader import RequestLoader
from .result_builder import ResultBuilder
from .runner import OrchestratorRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a test workflow runner workflow from JSON.")
    parser.add_argument("request_json", type=Path, help="Workflow request JSON path.")
    parser.add_argument("result_json", type=Path, nargs="?", default=None, help="Result JSON output path.")
    parser.add_argument("--result-json", dest="result_json_option", type=Path, default=None, help="Result JSON output path.")
    parser.add_argument("--dry-run", action="store_true", help="Run without loading real env_map or TAF bindings.")
    parser.add_argument("--repository-root", type=Path, default=None, help="Root path containing configs/env_map.json.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    loader = RequestLoader(args.repository_root, require_env_map=not args.dry_run)
    request = loader.load_json_file(args.request_json)
    if args.dry_run:
        request.runtime_options.dry_run = True
        context = build_dry_run_context(request)
    else:
        resolver = EnvConfigResolver(args.repository_root)
        context = resolver.load_testline_context(request.testline)
    runner = OrchestratorRunner()
    result_builder = ResultBuilder()
    state = runner.execute(request, context, OrchestratorState(), write_stdout=print, write_stderr=print)
    result_json = args.result_json_option or args.result_json or Path("result.json")
    result = result_builder.build_success(
        request,
        context,
        state,
        timestamps={"created_at": None, "started_at": state.kpi_test_starttime, "completed_at": state.kpi_test_endtime},
        artifacts={"request_json_path": str(args.request_json), "result_json_path": str(result_json), "extra_artifacts": []},
    )
    if state.status == "failed":
        result = result_builder.build_failure(
            request,
            state,
            error_message=state.error_message or "Workflow failed.",
            timestamps={"created_at": None, "started_at": state.kpi_test_starttime, "completed_at": state.kpi_test_endtime},
            artifacts={"request_json_path": str(args.request_json), "result_json_path": str(result_json), "extra_artifacts": []},
            context=context,
        )
    result_builder.write(result, result_json)
    return 0 if state.status == "completed" else 1


def build_dry_run_context(request: KpiTestModelRequest) -> TestlineContext:
    resolved = request.testline_resolution
    repository_root = resolved.config_path if resolved.config_path.suffix == "" else resolved.config_path.parent
    selected_ues = []
    for ue in (request.payload.get("ue_selection") or {}).get("selected_ues") or []:
        ue_index = int(ue["ue_index"])
        selected_ues.append(
            NormalizedUe(
                ue_index=ue_index,
                ue_type=str(ue["ue_type"]).strip().lower(),
                ue_ip=ue.get("ue_ip"),
                label=str(ue.get("label") or f"ue-{ue_index}"),
                serial_number=ue.get("serial_number"),
                capabilities=[str(value) for value in ue.get("capabilities") or []],
                raw_object=dict(ue),
            )
        )
    return TestlineContext(
        testline=request.testline,
        resolved_config=resolved,
        tl=SimpleNamespace(ues=selected_ues, gnbs=[], enbs=[]),
        repository_root=repository_root,
        ues=selected_ues,
        gnbs=[],
        enbs=[],
        raw_summary={
            "source": "cli_dry_run_request",
            "ue_count": len(selected_ues),
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
