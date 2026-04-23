from __future__ import annotations

from typing import Any

from .models import NormalizedUe


class UeExtractor:
    def extract(self, tl: Any) -> list[NormalizedUe]:
        candidates = list(getattr(tl, "ues", []) or [])
        normalized: list[NormalizedUe] = []
        for index, ue in enumerate(candidates, start=1):
            normalized.append(
                NormalizedUe(
                    ue_index=int(getattr(ue, "ue_index", index)),
                    ue_type=str(getattr(ue, "ue_type", getattr(ue, "type", "unknown"))).strip().lower(),
                    ue_ip=getattr(ue, "ue_ip", getattr(ue, "ip", None)),
                    label=str(getattr(ue, "label", f"ue-{index}")),
                    serial_number=getattr(ue, "serial_number", None),
                    capabilities=list(getattr(ue, "capabilities", []) or []),
                    raw_object=ue,
                )
            )
        return normalized

    def extract_summary(self, tl: Any) -> dict[str, Any]:
        ues = list(getattr(tl, "ues", []) or [])
        return {
            "ue_count": len(ues),
            "gnb_count": len(list(getattr(tl, "gnbs", []) or [])),
            "enb_count": len(list(getattr(tl, "enbs", []) or [])),
        }
