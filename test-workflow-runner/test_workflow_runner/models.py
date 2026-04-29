from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


SUPPORTED_TRAFFIC_MODELS = (
    "apply_preconditions",
    "attach",
    "handover",
    "dl_traffic",
    "ul_traffic",
    "swap",
    "detach",
    "syslog_check",
    "kpi_generator",
    "kpi_detector",
)


def normalize_testline(testline: str) -> str:
    return str(testline or "").strip()


def derive_testline_alias(testline: str) -> str:
    cleaned = normalize_testline(testline)
    aliases = re.findall(r"T\d+", cleaned.upper())
    return aliases[-1] if aliases else cleaned.upper()


@dataclass
class ResolvedConfig:
    testline: str
    config_id: str
    config_path: Path
    department: Optional[str] = None
    site: Optional[str] = None
    topology_id: Optional[str] = None
    match_type: str = "static_map"
    confidence: str = "high"
    allowed_script_roots: list[str] = field(default_factory=list)


@dataclass
class NormalizedUe:
    ue_index: int
    ue_type: str
    ue_ip: Optional[str]
    label: str
    serial_number: Optional[str] = None
    capabilities: list[str] = field(default_factory=list)
    raw_object: Any = None


@dataclass
class TestlineContext:
    testline: str
    resolved_config: ResolvedConfig
    tl: Any
    repository_root: Path | None = None
    ues: list[NormalizedUe] = field(default_factory=list)
    gnbs: list[Any] = field(default_factory=list)
    enbs: list[Any] = field(default_factory=list)
    appserver: Any = None
    test_pc: Any = None
    raw_summary: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeOptions:
    dry_run: bool = False
    stop_on_failure: bool = True
    max_parallel_workers: int = 4
    log_level: str = "INFO"
    bindings_module: Optional[str] = None


@dataclass
class UeScope:
    mode: str = "all_selected_ues"
    ue_indexes: list[int] = field(default_factory=list)
    ue_types: list[str] = field(default_factory=list)


@dataclass
class TrafficItem:
    item_id: str
    model: str
    enabled: bool
    order: int
    execution_mode: str
    continue_on_failure: bool
    ue_scope: UeScope
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class TrafficStage:
    stage_id: int
    stage_name: str
    execution_mode: str
    items: list[TrafficItem] = field(default_factory=list)


@dataclass
class HandlerResult:
    model: str
    status: str
    started_at: str
    completed_at: Optional[str]
    summary: dict[str, Any] = field(default_factory=dict)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    used_ues: list[int] = field(default_factory=list)
    params_echo: dict[str, Any] = field(default_factory=dict)
    stage_id: Optional[int] = None
    item_id: Optional[str] = None


@dataclass
class OrchestratorState:
    status: str = "queued"
    kpi_test_starttime: Optional[str] = None
    kpi_test_endtime: Optional[str] = None
    precondition_results: list[HandlerResult] = field(default_factory=list)
    traffic_results: list[HandlerResult] = field(default_factory=list)
    sidecar_results: list[HandlerResult] = field(default_factory=list)
    followup_results: list[HandlerResult] = field(default_factory=list)
    validation_warnings: list[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class KpiTestModelRequest:
    payload: dict[str, Any]
    testline: str
    runtime_options: RuntimeOptions
    testline_resolution: Optional[ResolvedConfig] = None

    def traffic_stages(self) -> list[TrafficStage]:
        stages = list((self.payload.get("traffic_plan") or {}).get("stages") or [])
        normalized: list[TrafficStage] = []
        for stage in stages:
            items: list[TrafficItem] = []
            for item in list(stage.get("items") or []):
                ue_scope_payload = item.get("ue_scope") or {}
                items.append(
                    TrafficItem(
                        item_id=str(item.get("item_id") or "").strip(),
                        model=str(item.get("model") or "").strip(),
                        enabled=bool(item.get("enabled", True)),
                        order=int(item.get("order") or 0),
                        execution_mode=str(item.get("execution_mode") or "serial").strip(),
                        continue_on_failure=bool(item.get("continue_on_failure", False)),
                        ue_scope=UeScope(
                            mode=str(ue_scope_payload.get("mode") or "all_selected_ues").strip(),
                            ue_indexes=[int(value) for value in list(ue_scope_payload.get("ue_indexes") or [])],
                            ue_types=[str(value).strip().lower() for value in list(ue_scope_payload.get("ue_types") or []) if str(value).strip()],
                        ),
                        params=dict(item.get("params") or {}),
                    )
                )
            normalized.append(
                TrafficStage(
                    stage_id=int(stage.get("stage_id") or 0),
                    stage_name=str(stage.get("stage_name") or "").strip() or f"stage-{int(stage.get('stage_id') or 0)}",
                    execution_mode=str(stage.get("execution_mode") or "serial").strip(),
                    items=sorted(items, key=lambda entry: entry.order),
                )
            )
        return sorted(normalized, key=lambda entry: entry.stage_id)

    def selected_ue_indexes(self) -> list[int]:
        selected = list((self.payload.get("ue_selection") or {}).get("selected_ues") or [])
        return [int(item["ue_index"]) for item in selected]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "KpiTestModelRequest":
        testline = normalize_testline(payload.get("testline") or "")
        runtime_payload = payload.get("runtime_options") or {}
        runtime_options = RuntimeOptions(
            dry_run=bool(runtime_payload.get("dry_run")),
            stop_on_failure=bool(runtime_payload.get("stop_on_failure", True)),
            max_parallel_workers=int(runtime_payload.get("max_parallel_workers") or 4),
            log_level=str(runtime_payload.get("log_level") or "INFO").upper(),
            bindings_module=str(runtime_payload.get("bindings_module") or "").strip() or None,
        )

        resolved_payload = payload.get("testline_resolution") or {}
        resolved_config = None
        if resolved_payload:
            resolved_config = ResolvedConfig(
                testline=testline,
                config_id=str(resolved_payload.get("config_id") or ""),
                config_path=Path(str(resolved_payload.get("config_path") or ".")),
                department=resolved_payload.get("department"),
                site=resolved_payload.get("site"),
                topology_id=resolved_payload.get("topology_id"),
                match_type=str(resolved_payload.get("match_type") or "static_map"),
                confidence=str(resolved_payload.get("confidence") or "high"),
                allowed_script_roots=list(resolved_payload.get("allowed_script_roots") or []),
            )

        return cls(
            payload=payload,
            testline=testline,
            runtime_options=runtime_options,
            testline_resolution=resolved_config,
        )

    @classmethod
    def from_json_file(cls, path: Path) -> "KpiTestModelRequest":
        payload = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(payload)
