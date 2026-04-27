from __future__ import annotations

from .base import BaseHandler, HandlerContext


class SyslogCheckHandler(BaseHandler):
    model_name = "syslog_check"
    result_bucket = "sidecars"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "syslog_check",
            {
                "mode": params.get("mode", "post_window_syslog_scan"),
                "severity_levels": list(params.get("severity_levels") or ["error", "warn"]),
                "window_source": params.get("window_source", "workflow"),
            },
        )
