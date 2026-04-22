from datetime import datetime
from zoneinfo import ZoneInfo

from app.repositories.run_repository import insert_run_record
from app.schemas.run import RunCreateRequest, RunCreateResponse


def run_create(request: RunCreateRequest) -> RunCreateResponse:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    timestamp = now.strftime("%Y%m%d%H%M%S%f")[:-3]
    run_id = f"run-{timestamp}"

    record = {
        "run_id": run_id,
        "testline": request.testline,
        "robotcase_path": request.robotcase_path,
        "status": "created",
        "message": "Run request accepted.",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    insert_run_record(record)

    return RunCreateResponse(
        run_id=record["run_id"],
        status=record["status"],
        message=record["message"],
    )
