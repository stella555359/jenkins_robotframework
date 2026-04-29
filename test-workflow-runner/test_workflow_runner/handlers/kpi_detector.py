from __future__ import annotations

from internal_tools.kpi_detector import run_detector_from_payload

from .base import BaseHandler, HandlerContext


class KpiDetectorHandler(BaseHandler):
    model_name = "kpi_detector"
    result_bucket = "followups"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        params.setdefault("environment", context.testline_context.resolved_config.config_id)
        params.setdefault("test_line", context.request.testline)
        if context.request.runtime_options.dry_run:
            return self.build_success(
                context,
                summary={
                    "implementation_mode": "internal_api_dry_run",
                    "action": "kpi_detector",
                    "environment": params["environment"],
                    "test_line": params["test_line"],
                    "source_file": params.get("source_file") or params.get("input_file"),
                },
            )

        try:
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
