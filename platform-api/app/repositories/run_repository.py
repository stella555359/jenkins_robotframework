import sqlite3
from pathlib import Path

from app.core.config import settings

CREATE_RUNS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    testline TEXT NOT NULL,
    robotcase_path TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
)
"""


def initialize_run_repository() -> None:
    db_path = Path(settings.runs_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(CREATE_RUNS_TABLE_SQL)
        connection.commit()


def insert_run_record(record: dict[str, str]) -> None:
    initialize_run_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.execute(
            """
            INSERT INTO runs (
                run_id,
                testline,
                robotcase_path,
                status,
                message,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["run_id"],
                record["testline"],
                record["robotcase_path"],
                record["status"],
                record["message"],
                record["created_at"],
                record["updated_at"],
            ),
        )
        connection.commit()


def list_run_records() -> list[dict[str, str]]:
    initialize_run_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                run_id,
                testline,
                robotcase_path,
                status,
                message,
                created_at,
                updated_at
            FROM runs
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]


def get_run_record_by_id(run_id: str) -> dict[str, str] | None:
    initialize_run_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT
                run_id,
                testline,
                robotcase_path,
                status,
                message,
                created_at,
                updated_at
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

    return dict(row) if row else None
