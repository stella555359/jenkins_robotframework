import json
import sqlite3
from pathlib import Path
from typing import Any

from app.core.config import settings


AI_ANALYSIS_COLUMNS: dict[str, str] = {
    "analysis_id": "TEXT PRIMARY KEY",
    "run_id": "TEXT NOT NULL",
    "analysis_status": "TEXT NOT NULL",
    "analysis_version": "TEXT NOT NULL",
    "analysis_mode": "TEXT NOT NULL DEFAULT 'cursor_sdk'",
    "request_json": "TEXT NOT NULL DEFAULT '{}'",
    "result_json": "TEXT NOT NULL DEFAULT '{}'",
    "report_markdown": "TEXT NOT NULL DEFAULT ''",
    "error_message": "TEXT NOT NULL DEFAULT ''",
    "created_at": "TEXT NOT NULL",
    "updated_at": "TEXT NOT NULL",
}

JSON_COLUMNS = {
    "request_json": "{}",
    "result_json": "{}",
}


def initialize_ai_analysis_repository() -> None:
    db_path = Path(settings.runs_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS ai_analysis (
                {", ".join(f"{name} {definition}" for name, definition in AI_ANALYSIS_COLUMNS.items())}
            )
            """
        )
        _ensure_ai_analysis_columns(connection)
        connection.commit()


def _ensure_ai_analysis_columns(connection: sqlite3.Connection) -> None:
    existing = {
        row[1]
        for row in connection.execute("PRAGMA table_info(ai_analysis)").fetchall()
    }
    for name, definition in AI_ANALYSIS_COLUMNS.items():
        if name in existing:
            continue
        connection.execute(f"ALTER TABLE ai_analysis ADD COLUMN {name} {definition}")


def _encode_record(record: dict[str, Any], *, fill_defaults: bool = True) -> dict[str, Any]:
    encoded = dict(record)
    for column, default in JSON_COLUMNS.items():
        if column not in encoded:
            if fill_defaults:
                encoded[column] = json.dumps(json.loads(default), ensure_ascii=False)
            continue
        value = encoded.get(column)
        encoded[column] = json.dumps(value if value is not None else json.loads(default), ensure_ascii=False)
    if fill_defaults:
        for column in AI_ANALYSIS_COLUMNS:
            encoded.setdefault(column, "" if "TEXT" in AI_ANALYSIS_COLUMNS[column] else 0)
    return encoded


def _decode_record(record: dict[str, Any]) -> dict[str, Any]:
    decoded = dict(record)
    for column, default in JSON_COLUMNS.items():
        raw_value = decoded.get(column)
        if raw_value in (None, ""):
            decoded[column] = json.loads(default)
        elif isinstance(raw_value, str):
            decoded[column] = json.loads(raw_value)
    return decoded


def insert_ai_analysis_record(record: dict[str, Any]) -> None:
    initialize_ai_analysis_repository()
    encoded = _encode_record(record)

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.execute(
            """
            INSERT INTO ai_analysis (
                analysis_id,
                run_id,
                analysis_status,
                analysis_version,
                analysis_mode,
                request_json,
                result_json,
                report_markdown,
                error_message,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                encoded["analysis_id"],
                encoded["run_id"],
                encoded["analysis_status"],
                encoded["analysis_version"],
                encoded["analysis_mode"],
                encoded["request_json"],
                encoded["result_json"],
                encoded["report_markdown"],
                encoded["error_message"],
                encoded["created_at"],
                encoded["updated_at"],
            ),
        )
        connection.commit()


def get_ai_analysis_record(analysis_id: str) -> dict[str, Any] | None:
    initialize_ai_analysis_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT *
            FROM ai_analysis
            WHERE analysis_id = ?
            """,
            (analysis_id,),
        ).fetchone()

    return _decode_record(dict(row)) if row else None


def get_latest_ai_analysis_record(run_id: str) -> dict[str, Any] | None:
    initialize_ai_analysis_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT *
            FROM ai_analysis
            WHERE run_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (run_id,),
        ).fetchone()

    return _decode_record(dict(row)) if row else None


def list_queued_ai_analysis_records(limit: int = 1) -> list[dict[str, Any]]:
    initialize_ai_analysis_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM ai_analysis
            WHERE analysis_status = 'queued'
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [_decode_record(dict(row)) for row in rows]


def update_ai_analysis_record(analysis_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    initialize_ai_analysis_repository()
    filtered = {key: value for key, value in updates.items() if key in AI_ANALYSIS_COLUMNS and key != "analysis_id"}
    if not filtered:
        return get_ai_analysis_record(analysis_id)

    encoded = _encode_record(filtered, fill_defaults=False)
    assignments = ", ".join(f"{column} = ?" for column in encoded)
    values = [encoded[column] for column in encoded]
    values.append(analysis_id)

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.execute(
            f"""
            UPDATE ai_analysis
            SET {assignments}
            WHERE analysis_id = ?
            """,
            values,
        )
        connection.commit()

    return get_ai_analysis_record(analysis_id)


def claim_queued_ai_analysis_record(analysis_id: str, *, updated_at: str) -> dict[str, Any] | None:
    initialize_ai_analysis_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        cursor = connection.execute(
            """
            UPDATE ai_analysis
            SET analysis_status = 'running', updated_at = ?
            WHERE analysis_id = ? AND analysis_status = 'queued'
            """,
            (updated_at, analysis_id),
        )
        connection.commit()

    if cursor.rowcount == 0:
        return None
    return get_ai_analysis_record(analysis_id)
