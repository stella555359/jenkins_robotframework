from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable, Sequence

from .kpi_detector import run_detector_from_payload
from .kpi_generator import run_generator_from_payload

ToolFunction = Callable[..., dict[str, Any]]

TOOL_FUNCTIONS: dict[str, ToolFunction] = {
    "kpi_generator": run_generator_from_payload,
    "kpi_detector": run_detector_from_payload,
}


def _artifact_manifest(tool_result: dict[str, Any], *, tool_kind: str) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for artifact in tool_result.get("artifacts") or []:
        if not isinstance(artifact, dict):
            continue
        normalized = dict(artifact)
        normalized.setdefault("source", tool_kind)
        normalized.setdefault("metadata", {})
        manifest.append(normalized)
    return manifest


def _prepare_payload(request_payload: dict[str, Any]) -> tuple[str, dict[str, Any], str | None]:
    tool_kind = str(request_payload.get("tool_kind") or "").strip()
    if tool_kind not in TOOL_FUNCTIONS:
        supported = ", ".join(sorted(TOOL_FUNCTIONS))
        raise ValueError(f"Unsupported tool_kind {tool_kind!r}. Supported values: {supported}.")

    payload = dict(request_payload.get("payload") or {})
    item_id = str(request_payload.get("item_id") or "").strip() or None
    output_dir = str(request_payload.get("output_dir") or "").strip()
    if output_dir:
        if tool_kind == "kpi_generator":
            payload.setdefault("output_dir", output_dir)
        else:
            payload.setdefault("runtime_root", output_dir)
    return tool_kind, payload, item_id


def run_tool_from_request(request_payload: dict[str, Any]) -> dict[str, Any]:
    tool_kind, payload, item_id = _prepare_payload(request_payload)
    tool_result = TOOL_FUNCTIONS[tool_kind](payload=payload, item_id=item_id)
    result = {
        "status": "completed",
        "tool_kind": tool_kind,
        "summary": tool_result.get("summary") or {},
        "artifacts": tool_result.get("artifacts") or [],
        "artifact_manifest": _artifact_manifest(tool_result, tool_kind=tool_kind),
        "kpi_summary": tool_result.get("generator_result") or {},
        "detector_summary": tool_result.get("detector_summary") or {},
    }
    if tool_kind == "kpi_generator":
        result["detector_summary"] = {}
    else:
        result["kpi_summary"] = {}
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a standalone internal KPI tool request.")
    parser.add_argument("--request-json", type=Path, required=True, help="Path to the internal tool request JSON.")
    parser.add_argument("--result-json", type=Path, required=True, help="Path to write the tool result JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    request_payload = json.loads(args.request_json.read_text(encoding="utf-8"))
    try:
        result = run_tool_from_request(request_payload)
    except Exception as exc:  # noqa: BLE001
        result = {
            "status": "failed",
            "tool_kind": str(request_payload.get("tool_kind") or "").strip(),
            "summary": {},
            "artifacts": [],
            "artifact_manifest": [],
            "kpi_summary": {},
            "detector_summary": {},
            "error_message": str(exc),
        }
        exit_code = 1
    else:
        exit_code = 0

    args.result_json.parent.mkdir(parents=True, exist_ok=True)
    args.result_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
