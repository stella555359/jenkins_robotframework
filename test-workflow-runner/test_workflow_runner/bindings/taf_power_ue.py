from __future__ import annotations

from typing import Any


def run_prepare_ue(context) -> dict[str, Any]:
    return _run_per_ue(context, "prepare_ue")


def run_attach(context) -> dict[str, Any]:
    return _run_per_ue(context, "attach")


def run_detach(context) -> dict[str, Any]:
    return _run_per_ue(context, "detach")


def run_ul_traffic(context) -> dict[str, Any]:
    return _run_per_ue(context, "ul_traffic")


def run_dl_traffic(context) -> dict[str, Any]:
    return _run_per_ue(context, "dl_traffic")


def run_handover(context) -> dict[str, Any]:
    return _run_context_action(context, "handover")


def run_site_reset(context) -> dict[str, Any]:
    return _run_context_action(context, "site_reset")


def run_ru_reset(context) -> dict[str, Any]:
    return _run_context_action(context, "ru_reset")


def run_rf_reset(context) -> dict[str, Any]:
    return _run_context_action(context, "rf_reset")


def run_cell_lock(context) -> dict[str, Any]:
    return _run_context_action(context, "cell_lock")


def run_cell_unlock(context) -> dict[str, Any]:
    return _run_context_action(context, "cell_unlock")


def run_cell_lock_unlock(context) -> dict[str, Any]:
    return _run_context_action(context, "cell_lock_unlock")


def run_alarm_check(context) -> dict[str, Any]:
    return _run_context_action(context, "alarm_check")


def run_syslog_check(context) -> dict[str, Any]:
    return _run_context_action(context, "syslog_check")


def _run_per_ue(context, action: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for normalized_ue in context.selected_ues:
        target = normalized_ue.raw_object
        callback = _find_callable(target, action)
        if callback is None:
            raise RuntimeError(
                f"UE {normalized_ue.label} ({normalized_ue.ue_type}) does not expose a callable for action '{action}'."
            )
        value = callback(**_public_params(context.item.params))
        results.append(
            {
                "ue_index": normalized_ue.ue_index,
                "label": normalized_ue.label,
                "ue_type": normalized_ue.ue_type,
                "ue_family": normalized_ue.ue_family,
                "result": value,
            }
        )
    return {"target_ues": results}


def _run_context_action(context, action: str) -> dict[str, Any]:
    tl = context.testline_context.tl
    callback = _find_callable(tl, action)
    if callback is None:
        raise RuntimeError(f"testline object does not expose a callable for action '{action}'.")
    result = callback(**_public_params(context.item.params))
    return {"result": result}


def _find_callable(target: Any, action: str):
    candidate_names = [
        action,
        f"run_{action}",
        action.replace("_", ""),
    ]
    for name in candidate_names:
        callback = getattr(target, name, None)
        if callable(callback):
            return callback
    return None


def _public_params(params: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in params.items() if not key.startswith("_")}
