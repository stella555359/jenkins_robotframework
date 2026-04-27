from __future__ import annotations

from collections import Counter

from .models import TrafficStage


MODEL_RESOURCE_DOMAINS = {
    "apply_preconditions": "gnb_control",
    "attach": "ue_lifecycle",
    "handover": "gnb_control",
    "dl_traffic": "traffic_plane",
    "ul_traffic": "traffic_plane",
    "swap": "gnb_control",
    "detach": "ue_lifecycle",
    "syslog_check": "observation",
    "kpi_generator": "followup",
    "kpi_detector": "followup",
}

SERIAL_ONLY_DOMAINS = {"gnb_control", "followup"}


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
