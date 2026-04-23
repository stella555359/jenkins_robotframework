from __future__ import annotations

from .base import BaseHandler, HandlerContext


class SwapHandler(BaseHandler):
    model_name = "swap"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "swap",
            {
                "swap_profile": params.get("swap_profile"),
                "swap_timeout_seconds": int(params.get("swap_timeout_seconds") or 300),
            },
        )
