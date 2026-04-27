from __future__ import annotations

from .base import BaseHandler, HandlerContext


class DetachHandler(BaseHandler):
    model_name = "detach"

    def run(self, context: HandlerContext):
        return self.execute_taf_action(
            context,
            "detach",
            {},
        )
