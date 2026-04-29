from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .models import HandlerResult, KpiTestModelRequest, OrchestratorState, TestlineContext


class ResultBuilder:
    def build_success(
        self,
        request: KpiTestModelRequest,
        context: TestlineContext,
        state: OrchestratorState,
        *,
        timestamps: dict[str, Any],
        artifacts: dict[str, Any],
    ) -> dict[str, Any]:
        all_results = self._collect_results(state)
        return {
            "status": state.status,
            "testline": request.testline,
            "testline_alias": context.resolved_config.config_id,
            "summary": {
                "precondition_count": len(state.precondition_results),
                "traffic_count": len(state.traffic_results),
                "sidecar_count": len(state.sidecar_results),
                "followup_count": len(state.followup_results),
                "validation_warnings": list(state.validation_warnings),
            },
            "kpi_test_starttime": state.kpi_test_starttime,
            "kpi_test_endtime": state.kpi_test_endtime,
            "timestamps": timestamps,
            "artifacts": artifacts,
            "artifact_manifest": self._build_artifact_manifest(artifacts, all_results),
            "timeline": self._build_timeline(state, all_results),
            "resolved_config": asdict(context.resolved_config),
            "results": {
                "preconditions": [asdict(item) for item in state.precondition_results],
                "traffic": [asdict(item) for item in state.traffic_results],
                "sidecars": [asdict(item) for item in state.sidecar_results],
                "followups": [asdict(item) for item in state.followup_results],
            },
        }

    def build_failure(
        self,
        request: KpiTestModelRequest,
        state: OrchestratorState,
        *,
        error_message: str,
        timestamps: dict[str, Any],
        artifacts: dict[str, Any],
        context: TestlineContext | None = None,
    ) -> dict[str, Any]:
        resolved_config = asdict(context.resolved_config) if context is not None else None
        all_results = self._collect_results(state)
        return {
            "status": "failed",
            "testline": request.testline,
            "testline_alias": context.resolved_config.config_id if context is not None else None,
            "summary": {
                "error_message": error_message,
                "validation_warnings": list(state.validation_warnings),
            },
            "kpi_test_starttime": state.kpi_test_starttime,
            "kpi_test_endtime": state.kpi_test_endtime,
            "timestamps": timestamps,
            "artifacts": artifacts,
            "artifact_manifest": self._build_artifact_manifest(artifacts, all_results),
            "timeline": self._build_timeline(state, all_results),
            "resolved_config": resolved_config,
            "results": {
                "preconditions": [asdict(item) for item in state.precondition_results],
                "traffic": [asdict(item) for item in state.traffic_results],
                "sidecars": [asdict(item) for item in state.sidecar_results],
                "followups": [asdict(item) for item in state.followup_results],
            },
        }

    def write(self, result: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    def _collect_results(self, state: OrchestratorState) -> list[tuple[str, HandlerResult]]:
        return [
            *[("preconditions", item) for item in state.precondition_results],
            *[("traffic", item) for item in state.traffic_results],
            *[("sidecars", item) for item in state.sidecar_results],
            *[("followups", item) for item in state.followup_results],
        ]

    def _build_timeline(self, state: OrchestratorState, results: list[tuple[str, HandlerResult]]) -> list[dict[str, Any]]:
        timeline: list[dict[str, Any]] = []
        if state.kpi_test_starttime:
            timeline.append(
                {
                    "event": "workflow_started",
                    "scope": "workflow",
                    "status": "running",
                    "started_at": state.kpi_test_starttime,
                    "completed_at": state.kpi_test_starttime,
                }
            )

        ordered_results = sorted(
            results,
            key=lambda entry: (
                entry[1].completed_at or entry[1].started_at or "",
                entry[1].started_at or "",
                str(entry[1].stage_id or ""),
                str(entry[1].item_id or ""),
            ),
        )
        for bucket, result in ordered_results:
            timeline.append(
                {
                    "event": f"item_{result.status}",
                    "scope": "item",
                    "bucket": bucket,
                    "status": result.status,
                    "model": result.model,
                    "stage_id": result.stage_id,
                    "item_id": result.item_id,
                    "started_at": result.started_at,
                    "completed_at": result.completed_at,
                }
            )

        if state.kpi_test_endtime:
            timeline.append(
                {
                    "event": f"workflow_{state.status}",
                    "scope": "workflow",
                    "status": state.status,
                    "started_at": state.kpi_test_endtime,
                    "completed_at": state.kpi_test_endtime,
                }
            )
        return timeline

    def _build_artifact_manifest(
        self,
        artifacts: dict[str, Any],
        results: list[tuple[str, HandlerResult]],
    ) -> list[dict[str, Any]]:
        manifest: list[dict[str, Any]] = []

        request_json_path = artifacts.get("request_json_path")
        if request_json_path:
            manifest.append(
                {
                    "kind": "workflow_request_json",
                    "label": "Workflow request JSON",
                    "path": str(request_json_path),
                    "content_type": "application/json",
                    "source": "cli",
                    "metadata": {},
                }
            )

        result_json_path = artifacts.get("result_json_path")
        if result_json_path:
            manifest.append(
                {
                    "kind": "workflow_result_json",
                    "label": "Workflow result JSON",
                    "path": str(result_json_path),
                    "content_type": "application/json",
                    "source": "runner",
                    "metadata": {},
                }
            )

        for extra_artifact in artifacts.get("extra_artifacts") or []:
            normalized = self._normalize_artifact(extra_artifact, source="runner", metadata={})
            if normalized is not None:
                manifest.append(normalized)

        for bucket, result in results:
            for artifact in result.artifacts:
                normalized = self._normalize_artifact(
                    artifact,
                    source=result.model,
                    metadata={
                        "bucket": bucket,
                        "stage_id": result.stage_id,
                        "item_id": result.item_id,
                        "status": result.status,
                    },
                )
                if normalized is not None:
                    manifest.append(normalized)

        return self._deduplicate_artifacts(manifest)

    def _normalize_artifact(
        self,
        artifact: Any,
        *,
        source: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any] | None:
        if isinstance(artifact, str):
            label = Path(artifact).name or artifact
            return {
                "kind": "artifact",
                "label": label,
                "path": artifact,
                "source": source,
                "metadata": {key: value for key, value in metadata.items() if value is not None},
            }

        if not isinstance(artifact, dict):
            return None

        artifact_metadata = dict(artifact.get("metadata") or {})
        artifact_metadata.update({key: value for key, value in metadata.items() if value is not None})
        path_value = artifact.get("path")
        url_value = artifact.get("url")
        label = str(artifact.get("label") or path_value or url_value or f"{source} artifact")
        normalized = {
            "kind": str(artifact.get("kind") or "artifact"),
            "label": label,
            "path": path_value,
            "url": url_value,
            "content_type": artifact.get("content_type"),
            "source": artifact.get("source") or source,
            "metadata": artifact_metadata,
        }
        return normalized

    def _deduplicate_artifacts(self, artifacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deduplicated: list[dict[str, Any]] = []
        seen: set[str] = set()
        for artifact in artifacts:
            signature = json.dumps(artifact, ensure_ascii=False, sort_keys=True)
            if signature in seen:
                continue
            seen.add(signature)
            deduplicated.append(artifact)
        return deduplicated
