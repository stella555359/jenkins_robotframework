from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import configure_runtime_paths
from .detector import KPIAnomalyDetector


def _truthy(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


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


def run_detector_from_payload(
    *,
    payload: dict[str, Any],
    item_id: str | None = None,
) -> dict[str, Any]:
    source_file = str(payload.get("source_file") or payload.get("input_file") or "").strip()
    if not source_file:
        raise ValueError("kpi_detector requires params.source_file or params.input_file.")

    source_path = Path(source_file)
    if not source_path.exists():
        raise FileNotFoundError(f"kpi_detector source file not found: {source_path}")

    runtime_root = Path(
        str(payload.get("runtime_root") or (Path.cwd() / "kpi-artifacts" / "kpi_detector" / (item_id or source_path.stem)))
    )
    reports_dir = Path(str(payload.get("reports_dir") or (runtime_root / "reports")))
    docs_dir = Path(str(payload.get("docs_dir") or (runtime_root / "docs")))
    configure_runtime_paths(
        runtime_root=runtime_root,
        data_dir=source_path.parent,
        reports_dir=reports_dir,
        docs_dir=docs_dir,
    )

    detector = KPIAnomalyDetector(
        source_path,
        sheet_name=payload.get("sheet_name"),
        history_sheet_name=payload.get("history_sheet_name"),
        history_filename=payload.get("history_filename"),
        report_suffix=payload.get("report_suffix"),
        allow_scout_summary=_truthy(payload.get("allow_scout_summary"), True),
    )
    detector.run(generate_html=_truthy(payload.get("generate_html"), True))

    report_outputs = dict(detector.report_outputs)
    artifacts = [
        item
        for item in (
            _artifact("detector_html_report", "Detector HTML Report", report_outputs.get("html_report_path")),
            _artifact("detector_excel_report", "Detector Excel Report", report_outputs.get("excel_report_path")),
            *[
                _artifact("detector_detail_html", f"Detector Detail HTML {index + 1}", path_value)
                for index, path_value in enumerate(report_outputs.get("detail_html_paths") or [])
            ],
            *[
                _artifact("detector_detail_excel", f"Detector Detail Excel {index + 1}", path_value)
                for index, path_value in enumerate(report_outputs.get("detail_excel_paths") or [])
            ],
        )
        if item is not None
    ]

    summary_record = detector.portal_current_record or {}
    return {
        "summary": {
            "implementation_mode": "internal_api",
            "source_file": str(source_path),
            "reports_dir": str(reports_dir),
            "matched_history_count": summary_record.get("matched_history_count"),
            "portal_summary": summary_record.get("portal_summary") or {},
            "stats": summary_record.get("stats") or {},
        },
        "artifacts": artifacts,
        "detector_summary": summary_record,
    }
