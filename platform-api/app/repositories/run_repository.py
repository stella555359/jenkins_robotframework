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
