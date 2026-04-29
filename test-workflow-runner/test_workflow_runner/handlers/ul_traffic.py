from __future__ import annotations

from .base import BaseHandler, HandlerContext


class UlTrafficHandler(BaseHandler):
    model_name = "ul_traffic"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        script_path = str(params.get("script_path") or "").strip()
        if script_path:
            resolved_script_path = self.resolve_repository_path(context, script_path)
            command = self.resolve_command(str(params.get("command") or "")) if params.get("command") else ["python", resolved_script_path]
            return self.execute_command(
                context,
                "ul_traffic",
                command,
                cwd=self.resolve_working_directory(context, params.get("working_directory")),
            )
        return self.execute_taf_action(
            context,
            "ul_traffic",
            {
                "traffic_profile": params.get("traffic_profile"),
                "duration_seconds": int(params.get("duration_seconds") or 300),
            },
        )
