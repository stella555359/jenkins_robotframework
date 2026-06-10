from __future__ import annotations

from .base import BaseHandler, HandlerContext


class KpiDetectorHandler(BaseHandler):
    model_name = "kpi_detector"
    result_bucket = "followups"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        params.setdefault("environment", context.testline_context.resolved_config.config_id)
        params.setdefault("test_line", context.request.testline)
        params.setdefault(
            "workflow_window",
            {
                "business_start_time": context.state.business_starttime or context.state.kpi_test_starttime,
                "business_end_time": context.state.business_endtime or context.state.kpi_test_endtime,
            },
        )
        if context.request.runtime_options.dry_run:
            return self.build_success(
                context,
                summary={
                    "implementation_mode": "internal_api_dry_run",
                    "action": "kpi_detector",
                    "environment": params["environment"],
                    "test_line": params["test_line"],
                    "source_file": params.get("source_file") or params.get("input_file"),
                    "workflow_window": params.get("workflow_window"),
                },
            )

        try:
            from internal_tools.kpi_detector.service import run_detector_from_payload

            result = run_detector_from_payload(payload=params, item_id=context.item.item_id)
        except Exception as exc:  # noqa: BLE001
            return self.build_failure(
                context,
                error_message=str(exc),
                summary={"implementation_mode": "internal_api"},
            )

        return self.build_success(
            context,
            summary=result["summary"],
            artifacts=result["artifacts"],
        )
