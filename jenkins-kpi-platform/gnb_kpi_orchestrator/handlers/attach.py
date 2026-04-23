from __future__ import annotations

from .base import BaseHandler, HandlerContext


class AttachHandler(BaseHandler):
    model_name = "attach"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "attach",
            {
                "attach_timeout_seconds": int(params.get("attach_timeout_seconds") or 120),
            },
        )
