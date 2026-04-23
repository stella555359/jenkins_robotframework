from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core import (
    CompassClient,
    KpiGeneratorRequest,
    KpiGeneratorResult,
    KpiGeneratorService,
    configure_logging,
)

SPECIAL_PARAM_KEYS = {
    "_stage_id",
    "output_dir",
    "result_json_path",
    "verbose",
    "compass_username",
    "compass_password",
}


def _artifact(kind: str, label: str, path_value: str | Path | None) -> dict[str, Any] | None:
    if not path_value:
        return None
    path = Path(path_value)
    return {
        "kind": kind,
        "label": label,
        "path": str(path),
        "metadata": {"exists": path.exists()},
    }


def _clean_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if key not in SPECIAL_PARAM_KEYS}


def run_generator_from_payload(
    *,
    payload: dict[str, Any],
    item_id: str | None = None,
) -> dict[str, Any]:
    output_dir = Path(
        str(payload.get("output_dir") or (Path.cwd() / "kpi-artifacts" / "kpi_generator" / (item_id or "default")))
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    result_json_path = payload.get("result_json_path")
    result_json = Path(str(result_json_path)) if result_json_path else None
    verbose = bool(payload.get("verbose", False))

    request = KpiGeneratorRequest.from_payload(_clean_payload(payload))
    client = CompassClient(
        username=str(payload.get("compass_username") or "").strip() or None,
        password=str(payload.get("compass_password") or "").strip() or None,
    )
    service = KpiGeneratorService(client=client, output_dir=output_dir, logger=configure_logging(verbose=verbose))
    result = service.run(request)

    if result_json is not None:
        result_json.parent.mkdir(parents=True, exist_ok=True)
        result_json.write_text(json.dumps(result.to_jsonable(), ensure_ascii=False, indent=2), encoding="utf-8")

    artifacts = [
        item
        for item in (
            _artifact("generator_report", "Generator KPI Report", result.report_file_path),
            _artifact("generator_result_json", "Generator Result JSON", result_json),
        )
        if item is not None
    ]

    return {
        "summary": _build_summary(result, output_dir),
        "artifacts": artifacts,
        "generator_result": result.to_jsonable(),
    }


def _build_summary(result: KpiGeneratorResult, output_dir: Path) -> dict[str, Any]:
    return {
        "implementation_mode": "internal_api",
        "output_dir": str(output_dir),
        "report_file_path": result.report_file_path,
        "final_filename": result.final_filename,
        "template_names": list(result.template_names),
        "combined_report_ids": list(result.combined_report_ids),
        "interval_report_ids": list(result.interval_report_ids),
        "summary": dict(result.summary),
        "failed_templates": list(result.failed_templates),
        "failed_intervals": list(result.failed_intervals),
        "final_failure": dict(result.final_failure),
    }
