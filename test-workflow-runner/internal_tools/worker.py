from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib import request as urllib_request

from .tool_runner import run_tool_from_request


def _clean_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def _request_json(
    *,
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib_request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_created_tool_runs(*, base_url: str, timeout_seconds: int = 30) -> list[dict[str, Any]]:
    payload = _request_json(
        url=f"{base_url.rstrip('/')}/api/kpi/tool-runs?status=created",
        timeout_seconds=timeout_seconds,
    )
    return [item for item in payload.get("items") or [] if isinstance(item, dict)]


def fetch_run_detail(*, base_url: str, run_id: str, timeout_seconds: int = 30) -> dict[str, Any]:
    return _request_json(
        url=f"{base_url.rstrip('/')}/api/runs/{run_id}",
        timeout_seconds=timeout_seconds,
    )


def post_worker_callback(
    *,
    base_url: str,
    run_id: str,
    payload: dict[str, Any],
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    return _request_json(
        url=f"{base_url.rstrip('/')}/api/runs/{run_id}/callbacks/worker",
        method="POST",
        payload=payload,
        timeout_seconds=timeout_seconds,
    )


def build_tool_request_from_run_detail(
    run_detail: dict[str, Any],
    *,
    output_root: Path,
) -> dict[str, Any]:
    if run_detail.get("executor_type") != "internal_tool":
        raise ValueError("Worker can only execute internal_tool run details.")

    metadata = dict(run_detail.get("metadata") or {})
    run_id = _clean_text(run_detail.get("run_id"))
    tool_kind = _clean_text(metadata.get("tool_kind"))
    if tool_kind not in {"kpi_generator", "kpi_detector"}:
        raise ValueError("metadata.tool_kind must be kpi_generator or kpi_detector.")

    tool_payload = metadata.get("tool_payload")
    if not isinstance(tool_payload, dict) or not tool_payload:
        raise ValueError("metadata.tool_payload must be a non-empty object.")

    output_dir = _clean_text(metadata.get("output_dir"))
    if output_dir is None:
        output_dir = str((output_root / tool_kind / (run_id or "standalone")).resolve())

    return {
        "run_id": run_id,
        "executor_type": "internal_tool",
        "tool_kind": tool_kind,
        "item_id": _clean_text(metadata.get("item_id")) or run_id or tool_kind,
        "payload": dict(tool_payload),
        "output_dir": output_dir,
    }


def build_callback_payload(
    *,
    status: str,
    message: str,
    tool_result: dict[str, Any] | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = tool_result or {}
    return {
        "status": status,
        "message": message,
        "started_at": started_at,
        "finished_at": finished_at,
        "metadata": metadata or {},
        "artifact_manifest": result.get("artifact_manifest") or result.get("artifacts") or [],
        "kpi_summary": result.get("kpi_summary") or {},
        "detector_summary": result.get("detector_summary") or {},
    }


def process_tool_run(
    *,
    base_url: str,
    run_summary: dict[str, Any],
    output_root: Path,
    timeout_seconds: int = 30,
    fetch_detail: Callable[..., dict[str, Any]] = fetch_run_detail,
    send_callback: Callable[..., dict[str, Any]] = post_worker_callback,
) -> dict[str, Any]:
    run_id = _clean_text(run_summary.get("run_id"))
    if run_id is None:
        raise ValueError("run_id is required.")

    started_at = _now_iso()
    send_callback(
        base_url=base_url,
        run_id=run_id,
        timeout_seconds=timeout_seconds,
        payload=build_callback_payload(
            status="running",
            message="Internal tool worker started.",
            started_at=started_at,
            metadata={"worker": "internal_tools.worker", "worker_status": "running"},
        ),
    )

    run_detail = fetch_detail(base_url=base_url, run_id=run_id, timeout_seconds=timeout_seconds)
    tool_request = build_tool_request_from_run_detail(run_detail, output_root=output_root)
    tool_kind = str(tool_request.get("tool_kind") or "")
    try:
        tool_result = run_tool_from_request(tool_request)
    except Exception as exc:  # noqa: BLE001
        tool_result = {
            "status": "failed",
            "tool_kind": tool_kind,
            "summary": {},
            "artifacts": [],
            "artifact_manifest": [],
            "kpi_summary": {},
            "detector_summary": {},
            "error_message": str(exc),
        }

    finished_at = _now_iso()
    success = tool_result.get("status") == "completed"
    final_status = "passed" if success else "failed"
    message = "Internal tool worker completed." if success else str(tool_result.get("error_message") or "Internal tool worker failed.")
    send_callback(
        base_url=base_url,
        run_id=run_id,
        timeout_seconds=timeout_seconds,
        payload=build_callback_payload(
            status=final_status,
            message=message,
            tool_result=tool_result,
            started_at=started_at,
            finished_at=finished_at,
            metadata={
                "worker": "internal_tools.worker",
                "worker_status": tool_result.get("status"),
                "tool_kind": tool_kind,
            },
        ),
    )
    return tool_result


def run_worker_once(
    *,
    base_url: str,
    output_root: Path,
    limit: int = 1,
    timeout_seconds: int = 30,
    fetch_runs: Callable[..., list[dict[str, Any]]] = fetch_created_tool_runs,
) -> int:
    runs = fetch_runs(base_url=base_url, timeout_seconds=timeout_seconds)[: max(limit, 0)]
    for run_summary in runs:
        process_tool_run(
            base_url=base_url,
            run_summary=run_summary,
            output_root=output_root,
            timeout_seconds=timeout_seconds,
        )
    return len(runs)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Poll platform-api and execute standalone internal KPI tool runs.")
    parser.add_argument("--platform-api-base-url", required=True, help="Base URL for platform-api, for example http://127.0.0.1:8000.")
    parser.add_argument("--output-root", type=Path, default=Path("kpi-artifacts") / "internal_tool_worker", help="Root directory for per-run tool outputs.")
    parser.add_argument("--poll-interval-seconds", type=float, default=10.0, help="Sleep time between polling iterations.")
    parser.add_argument("--limit", type=int, default=1, help="Maximum created runs to process per polling iteration.")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="HTTP timeout for platform-api requests.")
    parser.add_argument("--once", action="store_true", help="Process one polling iteration and exit.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    while True:
        processed_count = run_worker_once(
            base_url=args.platform_api_base_url,
            output_root=output_root,
            limit=args.limit,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps({"processed_count": processed_count, "output_root": str(output_root)}, ensure_ascii=False))
        if args.once:
            return 0
        time.sleep(args.poll_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
