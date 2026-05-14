from __future__ import annotations

from .base import BaseHandler, HandlerContext


class DetachHandler(BaseHandler):
    model_name = "detach"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "detach",
            {
                "detach_mode": params.get("detach_mode"),
                "timeout_seconds": int(params.get("timeout_seconds") or params.get("detach_timeout_seconds") or 120),
            },
        )
