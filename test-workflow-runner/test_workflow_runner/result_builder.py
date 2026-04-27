from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import KpiTestModelRequest, OrchestratorState, TestlineContext


class ResultBuilder:
    def build_success(
        self,
        request: KpiTestModelRequest,
        context: TestlineContext,
        state: OrchestratorState,
        *,
        timestamps: dict[str, Any],
        artifacts: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "status": state.status,
            "env": request.env,
            "summary": {
                "precondition_count": len(state.precondition_results),
                "traffic_count": len(state.traffic_results),
                "sidecar_count": len(state.sidecar_results),
                "followup_count": len(state.followup_results),
                "validation_warnings": list(state.validation_warnings),
            },
            "kpi_test_starttime": state.kpi_test_starttime,
            "kpi_test_endtime": state.kpi_test_endtime,
            "timestamps": timestamps,
            "artifacts": artifacts,
            "resolved_config": asdict(context.resolved_config),
            "results": {
                "preconditions": [asdict(item) for item in state.precondition_results],
                "traffic": [asdict(item) for item in state.traffic_results],
                "sidecars": [asdict(item) for item in state.sidecar_results],
                "followups": [asdict(item) for item in state.followup_results],
            },
        }

    def build_failure(
        self,
        request: KpiTestModelRequest,
        state: OrchestratorState,
        *,
        error_message: str,
        timestamps: dict[str, Any],
        artifacts: dict[str, Any],
        context: TestlineContext | None = None,
    ) -> dict[str, Any]:
        resolved_config = asdict(context.resolved_config) if context is not None else None
        return {
            "status": "failed",
            "env": request.env,
            "summary": {
                "error_message": error_message,
                "validation_warnings": list(state.validation_warnings),
            },
            "kpi_test_starttime": state.kpi_test_starttime,
            "kpi_test_endtime": state.kpi_test_endtime,
            "timestamps": timestamps,
            "artifacts": artifacts,
            "resolved_config": resolved_config,
            "results": {
                "preconditions": [asdict(item) for item in state.precondition_results],
                "traffic": [asdict(item) for item in state.traffic_results],
                "sidecars": [asdict(item) for item in state.sidecar_results],
                "followups": [asdict(item) for item in state.followup_results],
            },
        }

    def write(self, result: dict[str, Any], path: Path) -> None:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
