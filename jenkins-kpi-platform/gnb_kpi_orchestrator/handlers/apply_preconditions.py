from __future__ import annotations

from .base import BaseHandler, HandlerContext


class ApplyPreconditionsHandler(BaseHandler):
    model_name = "apply_preconditions"
    result_bucket = "preconditions"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "apply_preconditions",
            {
                "requested_preconditions": {
                    "cell_barred": params.get("cell_barred"),
                    "pa_port_state": params.get("pa_port_state"),
                    "notes": params.get("notes"),
                },
            },
        )
