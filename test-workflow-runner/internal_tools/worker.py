from __future__ import annotations

import argparse
import io
import json
import sys
import threading
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Sequence
from urllib import request as urllib_request

from .tool_runner import run_tool_from_request

_PROGRESS_PREFIX = "__KPI_PROGRESS__ "


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


def fetch_running_tool_runs(*, base_url: str, timeout_seconds: int = 30) -> list[dict[str, Any]]:
    payload = _request_json(
        url=f"{base_url.rstrip('/')}/api/kpi/tool-runs?status=running",
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


def post_progress_events(
    *,
    base_url: str,
    run_id: str,
    events: list[dict[str, Any]],
    timeout_seconds: int = 10,
) -> None:
    if not events:
        return
    try:
        _request_json(
            url=f"{base_url.rstrip('/')}/api/runs/{run_id}/progress",
            method="POST",
            payload={"events": events},
            timeout_seconds=timeout_seconds,
        )
    except Exception:
        pass  # Best effort


def create_tool_run(
    *,
    base_url: str,
    tool_kind: str,
    payload: dict[str, Any],
    testline: str | None = None,
    build: str | None = None,
    metadata: dict[str, Any] | None = None,
    timeout_seconds: int = 30,
) -> dict[str, Any]:
    return _request_json(
        url=f"{base_url.rstrip('/')}/api/kpi/tool-runs",
        method="POST",
        payload={
            "tool_kind": tool_kind,
            "payload": payload,
            "testline": testline,
            "build": build,
            "metadata": metadata or {},
        },
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


class _ProgressCapture(io.TextIOBase):
    """Captures stdout lines that start with __KPI_PROGRESS__ prefix."""

    def __init__(self, original_stdout: io.TextIOBase) -> None:
        super().__init__()
        self._original = original_stdout
        self._lock = threading.Lock()
        self._events: list[dict[str, Any]] = []

    def write(self, text: str) -> int:
        self._original.write(text)
        for line in text.splitlines():
            if line.startswith(_PROGRESS_PREFIX):
                try:
                    event = json.loads(line[len(_PROGRESS_PREFIX):])
                    if isinstance(event, dict):
                        with self._lock:
                            self._events.append(event)
                except (json.JSONDecodeError, TypeError):
                    pass
        return len(text)

    def flush(self) -> None:
        self._original.flush()

    def drain_events(self) -> list[dict[str, Any]]:
        with self._lock:
            drained = list(self._events)
            self._events.clear()
        return drained


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

    # Capture progress events from stdout
    capture = _ProgressCapture(sys.stdout)
    original_stdout = sys.stdout

    tool_result: dict[str, Any] = {}
    try:
        sys.stdout = capture  # type: ignore[assignment]

        # Run tool in a thread so we can flush progress periodically
        result_holder: list[dict[str, Any]] = []
        error_holder: list[Exception] = []

        def _run() -> None:
            try:
                result_holder.append(run_tool_from_request(tool_request))
            except Exception as exc:  # noqa: BLE001
                error_holder.append(exc)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        while thread.is_alive():
            thread.join(timeout=3.0)
            events = capture.drain_events()
            if events:
                post_progress_events(base_url=base_url, run_id=run_id, events=events)

        # Flush remaining events
        events = capture.drain_events()
        if events:
            post_progress_events(base_url=base_url, run_id=run_id, events=events)

        if error_holder:
            raise error_holder[0]
        tool_result = result_holder[0] if result_holder else {}

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
    finally:
        sys.stdout = original_stdout

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

    # Auto-chain: if generator succeeded and auto_detect is enabled, create detector run
    if success and tool_kind == "kpi_generator":
        _maybe_auto_chain_detector(
            base_url=base_url,
            run_detail=run_detail,
            tool_result=tool_result,
            timeout_seconds=timeout_seconds,
        )

    return tool_result


def _maybe_auto_chain_detector(
    *,
    base_url: str,
    run_detail: dict[str, Any],
    tool_result: dict[str, Any],
    timeout_seconds: int = 30,
) -> None:
    metadata = run_detail.get("metadata") or {}
    if not metadata.get("auto_detect"):
        return

    kpi_summary = tool_result.get("kpi_summary") or {}
    summary = kpi_summary.get("summary") or kpi_summary
    report_path = summary.get("report_file_path") or kpi_summary.get("report_file_path")
    if not report_path:
        return

    testline = _clean_text(run_detail.get("testline")) or "standalone"
    build = _clean_text(run_detail.get("build")) or ""
    generator_run_id = _clean_text(run_detail.get("run_id")) or ""

    try:
        create_tool_run(
            base_url=base_url,
            tool_kind="kpi_detector",
            payload={
                "source_file": report_path,
                "generate_html": "true",
                "allow_scout_summary": "true",
            },
            testline=testline,
            build=build,
            metadata={
                "chained_from": generator_run_id,
                "auto_detect": False,
            },
            timeout_seconds=timeout_seconds,
        )
    except Exception:
        pass  # Best effort


def _get_tool_kind(run_summary: dict[str, Any]) -> str | None:
    """Extract tool_kind from run summary metadata or workflow_name."""
    metadata = run_summary.get("metadata") or {}
    if isinstance(metadata, dict):
        tk = _clean_text(metadata.get("tool_kind"))
        if tk:
            return tk
    # Fallback: workflow_name stores tool_kind for internal_tool runs
    wn = _clean_text(run_summary.get("workflow_name"))
    if wn in {"kpi_generator", "kpi_detector"}:
        return wn
    return None


def _classify_runs(runs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split runs into generator and detector lists."""
    generators: list[dict[str, Any]] = []
    detectors: list[dict[str, Any]] = []
    for run in runs:
        tk = _get_tool_kind(run)
        if tk == "kpi_generator":
            generators.append(run)
        elif tk == "kpi_detector":
            detectors.append(run)
    return generators, detectors


def _filter_detector_runs_by_testline_exclusivity(
    detector_runs: list[dict[str, Any]],
    running_runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """For detectors, only allow one run per testline at a time.

    If a testline already has a running detector, skip created ones for that testline.
    Among created ones for the same testline, only pick the oldest (first).
    """
    busy_testlines: set[str] = set()
    for run in running_runs:
        tk = _get_tool_kind(run)
        if tk == "kpi_detector":
            tl = (run.get("testline") or "").strip().lower()
            if tl:
                busy_testlines.add(tl)

    per_testline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in detector_runs:
        tl = (run.get("testline") or "standalone").strip().lower()
        per_testline[tl].append(run)

    eligible: list[dict[str, Any]] = []
    for testline, group in per_testline.items():
        if testline in busy_testlines:
            continue
        # Sort by created_at ascending, pick the first
        group.sort(key=lambda r: r.get("created_at") or "")
        eligible.append(group[0])

    return eligible


def run_worker_once(
    *,
    base_url: str,
    output_root: Path,
    limit: int = 10,
    max_workers: int = 4,
    timeout_seconds: int = 30,
    fetch_runs: Callable[..., list[dict[str, Any]]] = fetch_created_tool_runs,
) -> int:
    created_runs = fetch_runs(base_url=base_url, timeout_seconds=timeout_seconds)
    if not created_runs:
        return 0

    generators, detectors = _classify_runs(created_runs)

    # Fetch currently running runs to enforce detector testline exclusivity
    running_runs: list[dict[str, Any]] = []
    if detectors:
        try:
            running_runs = fetch_running_tool_runs(base_url=base_url, timeout_seconds=timeout_seconds)
        except Exception:
            pass

    eligible_detectors = _filter_detector_runs_by_testline_exclusivity(detectors, running_runs)

    # All generators can run in parallel; eligible detectors (one per testline) also parallel
    to_process = generators[:limit] + eligible_detectors[:limit]
    if not to_process:
        return 0

    processed = 0
    effective_workers = min(max_workers, len(to_process))

    if effective_workers <= 1:
        for run_summary in to_process:
            process_tool_run(
                base_url=base_url,
                run_summary=run_summary,
                output_root=output_root,
                timeout_seconds=timeout_seconds,
            )
            processed += 1
    else:
        with ThreadPoolExecutor(max_workers=effective_workers) as pool:
            futures = {
                pool.submit(
                    process_tool_run,
                    base_url=base_url,
                    run_summary=run_summary,
                    output_root=output_root,
                    timeout_seconds=timeout_seconds,
                ): run_summary
                for run_summary in to_process
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    run_id = _clean_text(futures[future].get("run_id")) or "unknown"
                    print(f"Worker error for {run_id}: {exc}")
                processed += 1

    return processed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Poll platform-api and execute standalone internal KPI tool runs.")
    parser.add_argument("--platform-api-base-url", required=True, help="Base URL for platform-api, for example http://127.0.0.1:8000.")
    parser.add_argument("--output-root", type=Path, default=Path("kpi-artifacts") / "internal_tool_worker", help="Root directory for per-run tool outputs.")
    parser.add_argument("--poll-interval-seconds", type=float, default=10.0, help="Sleep time between polling iterations.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum created runs to process per polling iteration.")
    parser.add_argument("--max-workers", type=int, default=4, help="Maximum concurrent tool executions.")
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
            max_workers=args.max_workers,
            timeout_seconds=args.timeout_seconds,
        )
        print(json.dumps({"processed_count": processed_count, "output_root": str(output_root)}, ensure_ascii=False))
        if args.once:
            return 0
        time.sleep(args.poll_interval_seconds)


if __name__ == "__main__":
    raise SystemExit(main())
