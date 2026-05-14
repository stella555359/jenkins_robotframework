from __future__ import annotations

from .base import BaseHandler, HandlerContext


class AlarmCheckHandler(BaseHandler):
    model_name = "alarm_check"
    result_bucket = "sidecars"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "alarm_check",
            {
                "window_source": params.get("window_source") or "workflow",
                "start_time": params.get("start_time"),
                "end_time": params.get("end_time"),
                "severity": params.get("severity"),
            },
        )
