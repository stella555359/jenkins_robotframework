from __future__ import annotations

from .base import BaseHandler, HandlerContext


class KpiGeneratorHandler(BaseHandler):
    model_name = "kpi_generator"
    result_bucket = "followups"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        params.setdefault("environment", context.testline_context.resolved_config.config_id)
        params.setdefault("test_line", context.request.testline)
        business_start = context.state.business_starttime or context.state.kpi_test_starttime
        business_end = context.state.business_endtime or context.state.kpi_test_endtime
        if business_start and business_end:
            params.setdefault("report_timestamps_list", [[business_start, business_end]])
        if context.request.runtime_options.dry_run:
            return self.build_success(
                context,
                summary={
                    "implementation_mode": "internal_api_dry_run",
                    "action": "kpi_generator",
                    "environment": params["environment"],
                    "test_line": params["test_line"],
                    "report_timestamps_list": params.get("report_timestamps_list"),
                    "requested_output_dir": params.get("output_dir"),
                },
            )

        try:
            from internal_tools.kpi_generator.service import run_generator_from_payload

            result = run_generator_from_payload(payload=params, item_id=context.item.item_id)
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
