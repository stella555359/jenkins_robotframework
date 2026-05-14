from __future__ import annotations

from typing import Any

from .models import NormalizedUe


UE_TYPE_BY_CAPABILITY = {
    "qct_dx50": "qct_dx50",
    "pioneer": "pioneer",
    "huawei_sigspark": "huawei_sigspark",
    "mtk": "mtk",
    "real_mediatek_ue": "mtk",
    "xiaomi": "xiaomi",
    "huawei": "huawei",
}

POWER_UE_CAPABILITY_CLASS_NAMES = {
    "Qualcomm",
    "Android",
    "TafUeFastmile",
    "TafUeAndroid",
    "TafUeAt",
    "TafUeMtk",
}

POWER_UE_CLASS_TRANSLATOR = {
    "MediaTek": "mtk",
}


def _clean_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _normalize_token(value: Any) -> str:
    return str(value or "").strip().lower()


class UeExtractor:
    def extract(self, tl: Any, *, module_globals: dict[str, Any] | None = None) -> list[NormalizedUe]:
        candidates = list(getattr(tl, "ues", []) or [])
        object_names = self._build_object_name_map(module_globals or {})
        normalized: list[NormalizedUe] = []
        for index, ue in enumerate(candidates, start=1):
            object_name = object_names.get(id(ue))
            capabilities = [str(value) for value in list(getattr(ue, "capabilities", []) or [])]
            inferred_type = self._infer_ue_type(ue, capabilities=capabilities, object_name=object_name)
            label = _clean_text(getattr(ue, "label", None)) or object_name or f"ue-{index}"
            normalized.append(
                NormalizedUe(
                    ue_index=int(getattr(ue, "ue_index", index)),
                    ue_type=inferred_type,
                    ue_ip=getattr(ue, "ue_ip", getattr(ue, "ip", None)),
                    label=label,
                    ue_family=self._infer_ue_family(inferred_type, capabilities=capabilities),
                    object_name=object_name,
                    serial_number=getattr(ue, "serial_number", None),
                    capabilities=capabilities,
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

    def _build_object_name_map(self, module_globals: dict[str, Any]) -> dict[int, str]:
        names: dict[int, str] = {}
        for name, value in module_globals.items():
            if not name.startswith("_"):
                continue
            if name.startswith("__"):
                continue
            names.setdefault(id(value), name)
        return names

    def _infer_ue_type(self, ue: Any, *, capabilities: list[str], object_name: str | None) -> str:
        explicit = _clean_text(getattr(ue, "ue_type", getattr(ue, "type", None)))
        if explicit and explicit.lower() not in {"unknown", "none"}:
            return explicit.lower()

        if isinstance(ue, dict):
            return self._infer_dict_ue_type(ue)

        capability_tokens = [_normalize_token(value) for value in capabilities]
        class_name_raw = ue.__class__.__name__
        if class_name_raw in POWER_UE_CAPABILITY_CLASS_NAMES and capability_tokens:
            return capability_tokens[-1]
        if class_name_raw in POWER_UE_CLASS_TRANSLATOR:
            translated = POWER_UE_CLASS_TRANSLATOR[class_name_raw]
            if capability_tokens and "mtk_lte" in capability_tokens[-1]:
                return capability_tokens[-1]
            return translated

        if capability_tokens:
            last_token = capability_tokens[-1]
            if last_token in UE_TYPE_BY_CAPABILITY:
                return UE_TYPE_BY_CAPABILITY[last_token]
            for token in capability_tokens:
                if token in UE_TYPE_BY_CAPABILITY:
                    return UE_TYPE_BY_CAPABILITY[token]

        object_token = _normalize_token(object_name)
        if "sigspark" in object_token:
            return "huawei_sigspark"
        if "android" in object_token:
            return "qct_dx50"
        if "mtk" in object_token:
            return "mtk"

        class_name = _normalize_token(class_name_raw)
        if "android" in class_name and "qct_dx50" in capability_tokens:
            return "qct_dx50"
        return class_name or "unknown"

    def _infer_ue_family(self, ue_type: str, *, capabilities: list[str]) -> str:
        capability_tokens = {_normalize_token(value) for value in capabilities}
        if ue_type in {"pioneer", "huawei_sigspark"} or "huawei_sigspark" in capability_tokens or "pioneer" in capability_tokens:
            return "pioneer"
        if ue_type in {"qct_dx50", "qualcomm"}:
            return "qualcomm"
        if ue_type in {"mtk", "mediatek"}:
            return "mediatek"
        return ue_type

    def _infer_dict_ue_type(self, ue: dict[str, Any]) -> str:
        pools = ue.get("UE_POOLS") or {}
        android_pool = pools.get("AndroidUePool") or {}
        inline_config = android_pool.get("inline_config") or {}
        first_key = _normalize_token(next(iter(inline_config.keys()), ""))
        if "askey" in first_key:
            return "askey"
        if "nokia_cpe" in first_key:
            return "nokia_cpe"
        if "cpe_lte" in first_key:
            return "cpe_lte"
        return "inseego"
