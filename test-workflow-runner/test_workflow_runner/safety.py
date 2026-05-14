from __future__ import annotations

from collections import Counter

from .models import NormalizedUe, TrafficItem, TrafficStage


MODEL_RESOURCE_DOMAINS = {
    "apply_preconditions": "gnb_control",
    "prepare_ue": "ue_lifecycle",
    "attach": "ue_lifecycle",
    "handover": "gnb_control",
    "dl_traffic": "traffic_plane",
    "ul_traffic": "traffic_plane",
    "swap": "gnb_control",
    "detach": "ue_lifecycle",
    "site_reset": "gnb_control",
    "ru_reset": "gnb_control",
    "rf_reset": "gnb_control",
    "cell_lock": "gnb_control",
    "cell_unlock": "gnb_control",
    "cell_lock_unlock": "gnb_control",
    "alarm_check": "observation",
    "syslog_check": "observation",
    "kpi_generator": "followup",
    "kpi_detector": "followup",
}

SERIAL_ONLY_DOMAINS = {"followup"}


def validate_parallel_stage(stage: TrafficStage) -> list[str]:
    if stage.execution_mode != "parallel":
        return []

    domains = [MODEL_RESOURCE_DOMAINS.get(item.model, "unknown") for item in stage.items if item.enabled]
    warnings: list[str] = []
    counts = Counter(domains)
    for domain, count in counts.items():
        if domain in SERIAL_ONLY_DOMAINS and count > 1:
            warnings.append(
                f"stage {stage.stage_id} requests parallel execution for {count} items in protected domain '{domain}'. "
                "Keep these items serial unless the resource boundary is explicitly isolated."
            )
    return warnings


def resource_keys_for_item(item: TrafficItem, selected_ues: list[NormalizedUe]) -> list[str]:
    domain = MODEL_RESOURCE_DOMAINS.get(item.model, "traffic_plane")
    params = item.params
    keys: set[str] = set()

    if domain == "ue_lifecycle":
        keys.update(f"ue:{ue.ue_index}" for ue in selected_ues)
    elif domain == "traffic_plane":
        keys.update(f"ue:{ue.ue_index}" for ue in selected_ues)
        appserver_id = params.get("appserver_id") or params.get("server_id") or params.get("iperf_server")
        if appserver_id:
            keys.add(f"appserver:{appserver_id}")
    elif domain == "gnb_control":
        gnb_id = params.get("gnb_id") or params.get("gnb_index") or "default"
        keys.add(f"gnb:{gnb_id}")
        cell_id = params.get("cell_id") or params.get("cell_name")
        if cell_id:
            keys.add(f"cell:{cell_id}")
        ru_id = params.get("ru_id") or params.get("ru_name")
        if ru_id:
            keys.add(f"ru:{ru_id}")
    elif domain == "followup":
        keys.add("kpi_followup")
    elif domain == "observation":
        keys.add("observation")

    return sorted(keys)
