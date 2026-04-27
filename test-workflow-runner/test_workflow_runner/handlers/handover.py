from __future__ import annotations

from .base import BaseHandler, HandlerContext


class HandoverHandler(BaseHandler):
    model_name = "handover"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "handover",
            {
                "handover_profile": params.get("handover_profile"),
                "handover_timeout_seconds": int(params.get("handover_timeout_seconds") or 300),
            },
        )
