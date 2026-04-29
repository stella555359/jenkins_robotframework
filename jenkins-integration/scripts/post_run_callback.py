from __future__ import annotations

import argparse
import json
from mimetypes import guess_type
from pathlib import Path
import time
from typing import Any, Callable, Sequence
from urllib import error as urllib_error
from urllib import request as urllib_request


def _clean_text(value: Any) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _load_json_file(path: Path | None, *, default: Any) -> Any:
    if path is None:
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def collect_artifact_manifest(*, artifact_dir: Path | None = None, artifact_paths: Sequence[Path] | None = None) -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    candidates: list[Path] = []
    if artifact_dir is not None and artifact_dir.exists():
        candidates.extend(path for path in sorted(artifact_dir.rglob("*")) if path.is_file())
    for path in artifact_paths or []:
        if path.exists() and path.is_file():
            candidates.append(path)

    seen: set[Path] = set()
    for path in candidates:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        content_type, _ = guess_type(resolved.name)
        manifest.append(
            {
                "kind": "artifact",
                "label": resolved.name,
                "path": str(resolved),
                "content_type": content_type,
                "metadata": {},
            }
        )
    return manifest


def build_callback_payload(
    *,
    status: str,
    message: str | None = None,
    jenkins_build_ref: str | None = None,
    started_at: str | None = None,
    finished_at: str | None = None,
    metadata: dict[str, Any] | None = None,
    artifact_manifest: list[dict[str, Any]] | None = None,
    kpi_summary: dict[str, Any] | None = None,
    detector_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if _clean_text(status) is None:
        raise ValueError("status is required.")
    return {
        "status": status,
        "message": _clean_text(message),
        "jenkins_build_ref": _clean_text(jenkins_build_ref),
        "started_at": _clean_text(started_at),
        "finished_at": _clean_text(finished_at),
        "metadata": metadata or {},
        "artifact_manifest": artifact_manifest or [],
        "kpi_summary": kpi_summary or {},
        "detector_summary": detector_summary or {},
    }


def send_callback(*, base_url: str, run_id: str, payload: dict[str, Any], timeout_seconds: int = 30) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/runs/{run_id}/callbacks/jenkins"
    request = urllib_request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib_request.urlopen(request, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def _write_json_file(path: Path | None, payload: Any) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def send_callback_with_retry(
    *,
    base_url: str,
    run_id: str,
    payload: dict[str, Any],
    timeout_seconds: int = 30,
    max_attempts: int = 3,
    backoff_seconds: float = 2.0,
    fallback_output_json: Path | None = None,
    ignore_send_failure: bool = False,
    send_operation: Callable[..., dict[str, Any]] | None = None,
    sleep_operation: Callable[[float], None] | None = None,
) -> dict[str, Any]:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1.")

    sender = send_operation or send_callback
    sleeper = sleep_operation or time.sleep
    attempts: list[dict[str, Any]] = []
    last_error: Exception | None = None

    for attempt_index in range(1, max_attempts + 1):
        try:
            response_payload = sender(
                base_url=base_url,
                run_id=run_id,
                payload=payload,
                timeout_seconds=timeout_seconds,
            )
            result = {
                "sent": True,
                "attempt_count": attempt_index,
                "attempts": attempts,
                "response": response_payload,
                "fallback_output_json": str(fallback_output_json) if fallback_output_json is not None else None,
            }
            return result
        except (urllib_error.URLError, urllib_error.HTTPError, TimeoutError, OSError, ValueError) as exc:
            last_error = exc
            attempts.append(
                {
                    "attempt": attempt_index,
                    "error": f"{exc.__class__.__name__}: {exc}",
                }
            )
            if attempt_index < max_attempts:
                sleeper(backoff_seconds * attempt_index)

    failure_payload = {
        "sent": False,
        "attempt_count": max_attempts,
        "attempts": attempts,
        "last_error": attempts[-1]["error"] if attempts else None,
        "callback_url": f"{base_url.rstrip('/')}/api/runs/{run_id}/callbacks/jenkins",
        "payload": payload,
        "fallback_output_json": str(fallback_output_json) if fallback_output_json is not None else None,
    }
    _write_json_file(fallback_output_json, failure_payload)

    if ignore_send_failure:
        return failure_payload

    assert last_error is not None
    raise last_error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and optionally POST a Jenkins callback payload to platform-api.")
    parser.add_argument("--run-id", type=str, required=True, help="Run id created by platform-api.")
    parser.add_argument("--status", type=str, required=True, help="Final run status to send to platform-api.")
    parser.add_argument("--message", type=str, default=None, help="Optional status message.")
    parser.add_argument("--jenkins-build-ref", type=str, default=None, help="Optional Jenkins build reference.")
    parser.add_argument("--started-at", type=str, default=None, help="Optional ISO timestamp for execution start.")
    parser.add_argument("--finished-at", type=str, default=None, help="Optional ISO timestamp for execution finish.")
    parser.add_argument("--metadata-json", type=Path, default=None, help="Optional metadata JSON file.")
    parser.add_argument("--artifact-manifest-json", type=Path, default=None, help="Optional prebuilt artifact manifest JSON file.")
    parser.add_argument("--artifact-dir", type=Path, default=None, help="Optional artifact directory to scan into artifact_manifest.")
    parser.add_argument("--artifact-path", type=Path, action="append", default=[], help="Optional artifact file path. Can be repeated.")
    parser.add_argument("--kpi-summary-json", type=Path, default=None, help="Optional KPI summary JSON file.")
    parser.add_argument("--detector-summary-json", type=Path, default=None, help="Optional detector summary JSON file.")
    parser.add_argument("--platform-api-base-url", type=str, default=None, help="Optional base URL used to POST callback payload.")
    parser.add_argument("--timeout-seconds", type=int, default=30, help="HTTP timeout used for each callback attempt.")
    parser.add_argument("--max-attempts", type=int, default=3, help="Maximum callback retry attempts.")
    parser.add_argument("--backoff-seconds", type=float, default=2.0, help="Linear backoff base seconds between callback retries.")
    parser.add_argument("--fallback-output-json", type=Path, default=None, help="Optional file path to persist callback payload and errors after final failure.")
    parser.add_argument("--send-result-json", type=Path, default=None, help="Optional file path to persist callback send result summary.")
    parser.add_argument("--ignore-send-failure", action="store_true", help="Do not exit non-zero when callback send fails after retries.")
    parser.add_argument("--output-json", type=Path, required=True, help="Path to write the callback payload JSON.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    artifact_manifest = list(_load_json_file(args.artifact_manifest_json, default=[]))
    artifact_manifest.extend(collect_artifact_manifest(artifact_dir=args.artifact_dir, artifact_paths=args.artifact_path))
    payload = build_callback_payload(
        status=args.status,
        message=args.message,
        jenkins_build_ref=args.jenkins_build_ref,
        started_at=args.started_at,
        finished_at=args.finished_at,
        metadata=dict(_load_json_file(args.metadata_json, default={})),
        artifact_manifest=artifact_manifest,
        kpi_summary=dict(_load_json_file(args.kpi_summary_json, default={})),
        detector_summary=dict(_load_json_file(args.detector_summary_json, default={})),
    )

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    output_text = json.dumps(payload, ensure_ascii=False, indent=2)
    args.output_json.write_text(output_text, encoding="utf-8")
    print(output_text)

    if args.platform_api_base_url:
        send_result = send_callback_with_retry(
            base_url=args.platform_api_base_url,
            run_id=args.run_id,
            payload=payload,
            timeout_seconds=args.timeout_seconds,
            max_attempts=args.max_attempts,
            backoff_seconds=args.backoff_seconds,
            fallback_output_json=args.fallback_output_json,
            ignore_send_failure=args.ignore_send_failure,
        )
        _write_json_file(args.send_result_json, send_result)
        print(json.dumps(send_result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
