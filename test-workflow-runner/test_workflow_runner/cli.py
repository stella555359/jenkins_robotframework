from __future__ import annotations

import argparse
from pathlib import Path

from .config_resolver import EnvConfigResolver
from .request_loader import RequestLoader
from .result_builder import ResultBuilder
from .runner import OrchestratorRunner
from .models import OrchestratorState


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a GNB KPI orchestrator workflow from JSON.")
    parser.add_argument("request_json", type=Path, help="Workflow request JSON path.")
    parser.add_argument("result_json", type=Path, help="Result JSON output path.")
    parser.add_argument("--repository-root", type=Path, default=None, help="Root path containing configs/env_map.json.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    loader = RequestLoader(args.repository_root)
    request = loader.load_json_file(args.request_json)
    resolver = EnvConfigResolver(args.repository_root)
    context = resolver.load_testline_context(request.env)
    runner = OrchestratorRunner()
    result_builder = ResultBuilder()
    state = runner.execute(request, context, OrchestratorState(), write_stdout=print, write_stderr=print)
    result = result_builder.build_success(
        request,
        context,
        state,
        timestamps={"created_at": None, "started_at": state.kpi_test_starttime, "completed_at": state.kpi_test_endtime},
        artifacts={"request_json_path": str(args.request_json), "result_json_path": str(args.result_json), "extra_artifacts": []},
    )
    if state.status == "failed":
        result = result_builder.build_failure(
            request,
            state,
            error_message=state.error_message or "Workflow failed.",
            timestamps={"created_at": None, "started_at": state.kpi_test_starttime, "completed_at": state.kpi_test_endtime},
            artifacts={"request_json_path": str(args.request_json), "result_json_path": str(args.result_json), "extra_artifacts": []},
            context=context,
        )
    result_builder.write(result, args.result_json)
    return 0 if state.status == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
