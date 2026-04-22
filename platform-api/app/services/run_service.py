import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from app.repositories.run_repository import (
    get_run_record_by_id,
    insert_run_record,
    list_run_records,
)
from app.schemas.run import (
    RunCreateRequest,
    RunCreateResponse,
    RunDetailResponse,
    RunListItem,
    RunListResponse,
)


def _build_run_id(timestamp: str, sequence: int) -> str:
    if sequence == 0:
        return f"run-{timestamp}"
    return f"run-{timestamp}-{sequence:02d}"


def run_create(request: RunCreateRequest) -> RunCreateResponse:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    timestamp = now.strftime("%Y%m%d%H%M%S%f")[:-3]
    record = {
        "testline": request.testline,
        "robotcase_path": request.robotcase_path,
        "status": "created",
        "message": "Run request accepted.",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    for sequence in range(0, 1000):
        record["run_id"] = _build_run_id(timestamp, sequence)
        try:
            insert_run_record(record)
            break
        except sqlite3.IntegrityError:
            continue
    else:
        raise RuntimeError("Failed to generate a unique run_id.")

    return RunCreateResponse(
        run_id=record["run_id"],
        status=record["status"],
        message=record["message"],
    )


def get_run_list() -> RunListResponse:
    records = list_run_records()
    return RunListResponse(items=[RunListItem(**record) for record in records])


def get_run_detail(run_id: str) -> RunDetailResponse:
    record = get_run_record_by_id(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    return RunDetailResponse(**record)
