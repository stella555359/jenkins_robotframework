from __future__ import annotations

from .base import BaseHandler, HandlerContext


def _repeat_count(params: dict) -> int:
    return int(params.get("repeat_count") or params.get("count") or 1)


class SiteResetHandler(BaseHandler):
    model_name = "site_reset"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "site_reset",
            {
                "gnb_id": params.get("gnb_id") or params.get("gnb_index") or "default",
                "repeat_count": _repeat_count(params),
                "timeout_seconds": int(params.get("timeout_seconds") or 900),
            },
        )


class RuResetHandler(BaseHandler):
    model_name = "ru_reset"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "ru_reset",
            {
                "gnb_id": params.get("gnb_id") or params.get("gnb_index") or "default",
                "ru_id": params.get("ru_id") or params.get("ru_name") or "default",
                "repeat_count": _repeat_count(params),
                "timeout_seconds": int(params.get("timeout_seconds") or 600),
            },
        )


class RfResetHandler(BaseHandler):
    model_name = "rf_reset"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "rf_reset",
            {
                "gnb_id": params.get("gnb_id") or params.get("gnb_index") or "default",
                "repeat_count": _repeat_count(params),
                "timeout_seconds": int(params.get("timeout_seconds") or 600),
            },
        )


class CellLockHandler(BaseHandler):
    model_name = "cell_lock"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "cell_lock",
            {
                "cell_id": params.get("cell_id") or params.get("cell_name"),
                "gnb_id": params.get("gnb_id") or params.get("gnb_index") or "default",
                "repeat_count": _repeat_count(params),
            },
        )


class CellUnlockHandler(BaseHandler):
    model_name = "cell_unlock"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "cell_unlock",
            {
                "cell_id": params.get("cell_id") or params.get("cell_name"),
                "gnb_id": params.get("gnb_id") or params.get("gnb_index") or "default",
                "repeat_count": _repeat_count(params),
            },
        )


class CellLockUnlockHandler(BaseHandler):
    model_name = "cell_lock_unlock"

    def run(self, context: HandlerContext):
        params = dict(context.item.params)
        return self.execute_taf_action(
            context,
            "cell_lock_unlock",
            {
                "cell_id": params.get("cell_id") or params.get("cell_name"),
                "gnb_id": params.get("gnb_id") or params.get("gnb_index") or "default",
                "repeat_count": _repeat_count(params),
                "lock_duration_seconds": int(params.get("lock_duration_seconds") or 30),
            },
        )
