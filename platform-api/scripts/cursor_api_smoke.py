#!/usr/bin/env python3
"""Smoke-test Cursor Cloud Agents REST API from a backend environment.

Runs three checks in order:
1. GET /v1/me
2. GET /v1/models
3. POST /v1/agents (no-repo cloud agent)

Usage:
  export CURSOR_API_KEY="crsr_..."
  export HTTPS_PROXY=http://proxy:8080   # if needed
  python scripts/cursor_api_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.cursor_rest_client import (  # noqa: E402
    CursorApiError,
    create_cloud_agent,
    get_me,
    list_models,
    wait_for_run,
)


def _print_section(title: str) -> None:
    print(f"\n=== {title} ===")


def _check_api_key() -> None:
    key = os.environ.get("CURSOR_API_KEY", "").strip()
    if not key:
        print("CURSOR_API_KEY is not set.")
        sys.exit(1)
    print(f"key_prefix: {key[:8]}")


def main() -> int:
    _check_api_key()

    _print_section("GET /v1/me")
    try:
        me = get_me()
        print(json.dumps(me, indent=2, ensure_ascii=False))
    except CursorApiError as exc:
        print(f"FAILED status={exc.status_code} code={exc.code} message={exc}")
        return 1

    _print_section("GET /v1/models")
    try:
        models = list_models()
        items = models.get("items") or models
        count = len(items) if isinstance(items, list) else "unknown"
        print(f"model_count: {count}")
        if isinstance(items, list) and items:
            print("first_model:", items[0].get("id") if isinstance(items[0], dict) else items[0])
    except CursorApiError as exc:
        print(f"FAILED status={exc.status_code} code={exc.code} message={exc}")
        return 1

    _print_section("POST /v1/agents (no-repo)")
    try:
        created = create_cloud_agent('Reply with exactly: {"ok": true, "message": "cursor rest works"}')
        print(json.dumps(created, indent=2, ensure_ascii=False)[:2000])
        agent_id = str((created.get("agent") or {}).get("id") or "")
        run_id = str((created.get("run") or {}).get("id") or (created.get("agent") or {}).get("latestRunId") or "")
        if not agent_id or not run_id:
            print("FAILED: create response missing agent/run ids")
            return 1
        print(f"agent_id={agent_id} run_id={run_id}")
        final_run = wait_for_run(agent_id, run_id)
        print("final_status:", final_run.get("status"))
        print("result_preview:", str(final_run.get("result") or "")[:500])
    except CursorApiError as exc:
        print(f"FAILED status={exc.status_code} code={exc.code} message={exc}")
        if exc.status_code == 403:
            print(
                "\n403 usually means Cloud Agents is not enabled for this account/key. "
                "See docs/modules/platform-api/guides/cursor-background-api-inventory.md"
            )
        return 1

    print("\nAll smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
