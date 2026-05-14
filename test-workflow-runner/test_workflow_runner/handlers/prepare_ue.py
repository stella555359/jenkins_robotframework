from __future__ import annotations

from .base import BaseHandler, HandlerContext


class PrepareUeHandler(BaseHandler):
    model_name = "prepare_ue"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "prepare_ue",
            {
                "ue_type_map": {ue.ue_index: ue.ue_type for ue in context.selected_ues},
                "ue_family_map": {ue.ue_index: ue.ue_family for ue in context.selected_ues},
                "attach_mode": params.get("attach_mode"),
                "retry": int(params.get("retry") or 0),
                "timeout_seconds": int(params.get("timeout_seconds") or params.get("timeout") or 300),
            },
        )
