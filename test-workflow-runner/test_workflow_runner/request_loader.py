from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config_resolver import EnvConfigResolver
from .models import (
    KpiTestModelRequest,
    ResolvedConfig,
    RuntimeOptions,
    SUPPORTED_TRAFFIC_MODELS,
    derive_testline_alias,
    normalize_testline,
)
from .safety import validate_parallel_stage


class RequestValidationError(ValueError):
    pass


class RequestLoader:
    def __init__(self, repository_root: Path | None = None, *, require_env_map: bool = True):
        self.repository_root = repository_root or Path(__file__).resolve().parents[1]
        self.require_env_map = require_env_map
        self.config_resolver = EnvConfigResolver(self.repository_root)

    def load_json_file(self, path: Path) -> KpiTestModelRequest:
        return self.load_dict(json.loads(path.read_text(encoding="utf-8")))

    def load_dict(self, payload: dict[str, Any]) -> KpiTestModelRequest:
        self.validate_payload(payload)
        request = KpiTestModelRequest.from_dict(payload)
        request.testline_resolution = self._load_resolved_config(payload)
        request.runtime_options = self._load_runtime_options(payload)
        return request

    def validate_payload(self, payload: dict[str, Any]) -> None:
        testline = normalize_testline(payload.get("testline") or "")
        if not testline:
            raise RequestValidationError("testline is required.")

        if self.require_env_map:
            self.config_resolver.resolve_testline(testline)

        ue_selection = payload.get("ue_selection") or {}
        if not isinstance(ue_selection, dict):
            raise RequestValidationError("ue_selection must be an object.")
        selected_ues = ue_selection.get("selected_ues") or []
        if not isinstance(selected_ues, list) or not selected_ues:
            raise RequestValidationError("selected_ues must contain at least one UE object.")
        seen_ue_indexes: set[int] = set()
        for selected_ue in selected_ues:
            if not isinstance(selected_ue, dict):
                raise RequestValidationError("Each selected UE must be an object.")
            missing_keys = [key for key in ("ue_index", "ue_type", "label") if key not in selected_ue]
            if missing_keys:
                missing_text = ", ".join(missing_keys)
                raise RequestValidationError(f"Each selected UE object must include: {missing_text}")
            try:
                ue_index = int(selected_ue["ue_index"])
            except (TypeError, ValueError) as exc:
                raise RequestValidationError("selected_ue.ue_index must be an integer.") from exc
            if ue_index in seen_ue_indexes:
                raise RequestValidationError(f"selected_ues contains duplicate ue_index: {ue_index}")
            seen_ue_indexes.add(ue_index)

        traffic_plan = payload.get("traffic_plan") or {}
        if not isinstance(traffic_plan, dict):
            raise RequestValidationError("traffic_plan must be an object.")
        stages = traffic_plan.get("stages") or []
        if not stages:
            raise RequestValidationError("traffic_plan.stages is required.")
        seen_stage_ids: set[int] = set()
        for stage in stages:
            if not isinstance(stage, dict):
                raise RequestValidationError("Each stage must be an object.")
            try:
                stage_id = int(stage.get("stage_id"))
            except (TypeError, ValueError) as exc:
                raise RequestValidationError("stage_id must be an integer.") from exc
            if stage_id in seen_stage_ids:
                raise RequestValidationError(f"Duplicate stage_id: {stage_id}")
            seen_stage_ids.add(stage_id)
            stage_mode = str(stage.get("execution_mode") or "").strip()
            if stage_mode not in {"serial", "parallel"}:
                raise RequestValidationError("stage.execution_mode must be serial or parallel.")
            items = stage.get("items") or []
            if not items:
                raise RequestValidationError(f"stage {stage_id} must contain at least one traffic item.")
            seen_item_ids: set[str] = set()
            for item in items:
                if not isinstance(item, dict):
                    raise RequestValidationError("Each traffic item must be an object.")
                item_id = str(item.get("item_id") or "").strip()
                if not item_id:
                    raise RequestValidationError("Each traffic item must define item_id.")
                if item_id in seen_item_ids:
                    raise RequestValidationError(f"Duplicate item_id within stage {stage_id}: {item_id}")
                seen_item_ids.add(item_id)
                model_name = str(item.get("model") or "").strip()
                if model_name not in SUPPORTED_TRAFFIC_MODELS:
                    supported_text = ", ".join(SUPPORTED_TRAFFIC_MODELS)
                    raise RequestValidationError(f"Only these traffic models are supported: {supported_text}")
                item_mode = str(item.get("execution_mode") or "").strip()
                if item_mode not in {"serial", "parallel"}:
                    raise RequestValidationError(f"{item_id}.execution_mode must be serial or parallel.")
                ue_scope = item.get("ue_scope") or {}
                if not isinstance(ue_scope, dict) or str(ue_scope.get("mode") or "").strip() == "":
                    raise RequestValidationError(f"{item_id}.ue_scope.mode is required.")
                if model_name in {"dl_traffic", "ul_traffic"}:
                    params = item.get("params") or {}
                    script_path = str(params.get("script_path") or "").strip()
                    if script_path and self.require_env_map:
                        self.config_resolver.validate_script_path(testline, script_path)

        request = KpiTestModelRequest.from_dict(payload)
        warnings: list[str] = []
        for stage in request.traffic_stages():
            warnings.extend(validate_parallel_stage(stage))
        if warnings:
            raise RequestValidationError(" ".join(warnings))

        runtime_options = payload.get("runtime_options") or {}
        if not isinstance(runtime_options, dict):
            raise RequestValidationError("runtime_options must be an object.")
        try:
            max_parallel_workers = int(runtime_options.get("max_parallel_workers") or 4)
        except (TypeError, ValueError) as exc:
            raise RequestValidationError("max_parallel_workers must be an integer.") from exc
        if max_parallel_workers <= 0:
            raise RequestValidationError("max_parallel_workers must be greater than 0.")

    def _load_resolved_config(self, payload: dict[str, Any]) -> ResolvedConfig:
        testline = normalize_testline(payload["testline"])
        testline_alias = derive_testline_alias(testline)
        provided = payload.get("testline_resolution") or {}
        if not self.require_env_map:
            return ResolvedConfig(
                testline=testline,
                config_id=str(provided.get("config_id") or testline_alias),
                config_path=self.repository_root / Path(str(provided.get("config_path") or ".")),
                department=provided.get("department"),
                site=provided.get("site"),
                topology_id=provided.get("topology_id"),
                match_type=str(provided.get("match_type") or "dry_run_request"),
                confidence=str(provided.get("confidence") or "low"),
                allowed_script_roots=list(provided.get("allowed_script_roots") or []),
            )
        resolved = self.config_resolver.resolve_testline(testline)
        if provided:
            config_id = str(provided.get("config_id") or "")
            if config_id and config_id != resolved.config_id:
                raise RequestValidationError("testline_resolution.config_id must match env_map.json.")
        return resolved

    def _load_runtime_options(self, payload: dict[str, Any]) -> RuntimeOptions:
        options = payload.get("runtime_options") or {}
        return RuntimeOptions(
            dry_run=bool(options.get("dry_run")),
            stop_on_failure=bool(options.get("stop_on_failure", True)),
            max_parallel_workers=int(options.get("max_parallel_workers") or 4),
            log_level=str(options.get("log_level") or "INFO").upper(),
            bindings_module=str(options.get("bindings_module") or "").strip() or None,
        )
