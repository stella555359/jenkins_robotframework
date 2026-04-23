import json
import sqlite3
from pathlib import Path
from typing import Any

from app.core.config import settings

RUN_COLUMNS: dict[str, str] = {
    "run_id": "TEXT PRIMARY KEY",
    "executor_type": "TEXT NOT NULL DEFAULT 'robot'",
    "workflow_name": "TEXT NOT NULL DEFAULT ''",
    "testline": "TEXT NOT NULL",
    "robotcase_path": "TEXT NOT NULL DEFAULT ''",
    "build": "TEXT NOT NULL DEFAULT ''",
    "scenario": "TEXT NOT NULL DEFAULT ''",
    "status": "TEXT NOT NULL",
    "message": "TEXT NOT NULL",
    "enable_kpi_generator": "INTEGER NOT NULL DEFAULT 0",
    "enable_kpi_anomaly_detector": "INTEGER NOT NULL DEFAULT 0",
    "workflow_spec_json": "TEXT NOT NULL DEFAULT '{}'",
    "run_metadata_json": "TEXT NOT NULL DEFAULT '{}'",
    "artifact_manifest_json": "TEXT NOT NULL DEFAULT '[]'",
    "kpi_config_json": "TEXT NOT NULL DEFAULT '{}'",
    "kpi_summary_json": "TEXT NOT NULL DEFAULT '{}'",
    "detector_summary_json": "TEXT NOT NULL DEFAULT '{}'",
    "jenkins_build_ref": "TEXT NOT NULL DEFAULT ''",
    "started_at": "TEXT NOT NULL DEFAULT ''",
    "finished_at": "TEXT NOT NULL DEFAULT ''",
    "created_at": "TEXT NOT NULL",
    "updated_at": "TEXT NOT NULL",
}

JSON_COLUMNS = {
    "workflow_spec_json": "{}",
    "run_metadata_json": "{}",
    "artifact_manifest_json": "[]",
    "kpi_config_json": "{}",
    "kpi_summary_json": "{}",
    "detector_summary_json": "{}",
}

BOOLEAN_COLUMNS = {
    "enable_kpi_generator",
    "enable_kpi_anomaly_detector",
}


def initialize_run_repository() -> None:
    db_path = Path(settings.runs_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS runs (
                {", ".join(f"{name} {definition}" for name, definition in RUN_COLUMNS.items())}
            )
            """
        )
        _ensure_run_columns(connection)
        connection.commit()


def _ensure_run_columns(connection: sqlite3.Connection) -> None:
    existing = {
        row[1]
        for row in connection.execute("PRAGMA table_info(runs)").fetchall()
    }
    for name, definition in RUN_COLUMNS.items():
        if name in existing:
            continue
        connection.execute(f"ALTER TABLE runs ADD COLUMN {name} {definition}")


def _encode_record(record: dict[str, Any], *, fill_defaults: bool = True) -> dict[str, Any]:
    encoded = dict(record)
    for column, default in JSON_COLUMNS.items():
        if column not in encoded:
            if fill_defaults:
                encoded[column] = json.dumps(json.loads(default), ensure_ascii=False)
            continue
        value = encoded.get(column)
        encoded[column] = json.dumps(value if value is not None else json.loads(default), ensure_ascii=False)
    for column in BOOLEAN_COLUMNS:
        if column in encoded:
            encoded[column] = 1 if bool(encoded.get(column)) else 0
        elif fill_defaults:
            encoded[column] = 0
    if fill_defaults:
        for column in RUN_COLUMNS:
            encoded.setdefault(column, "" if "TEXT" in RUN_COLUMNS[column] else 0)
    return encoded


def _decode_record(record: dict[str, Any]) -> dict[str, Any]:
    decoded = dict(record)
    for column, default in JSON_COLUMNS.items():
        raw_value = decoded.get(column)
        if raw_value in (None, ""):
            decoded[column] = json.loads(default)
        elif isinstance(raw_value, str):
            decoded[column] = json.loads(raw_value)
    for column in BOOLEAN_COLUMNS:
        decoded[column] = bool(decoded.get(column))
    return decoded


def insert_run_record(record: dict[str, Any]) -> None:
    initialize_run_repository()
    encoded = _encode_record(record)

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.execute(
            """
            INSERT INTO runs (
                run_id,
                executor_type,
                workflow_name,
                testline,
                robotcase_path,
                build,
                scenario,
                status,
                message,
                enable_kpi_generator,
                enable_kpi_anomaly_detector,
                workflow_spec_json,
                run_metadata_json,
                artifact_manifest_json,
                kpi_config_json,
                kpi_summary_json,
                detector_summary_json,
                jenkins_build_ref,
                started_at,
                finished_at,
                created_at,
                updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                encoded["run_id"],
                encoded["executor_type"],
                encoded["workflow_name"],
                encoded["testline"],
                encoded["robotcase_path"],
                encoded["build"],
                encoded["scenario"],
                encoded["status"],
                encoded["message"],
                encoded["enable_kpi_generator"],
                encoded["enable_kpi_anomaly_detector"],
                encoded["workflow_spec_json"],
                encoded["run_metadata_json"],
                encoded["artifact_manifest_json"],
                encoded["kpi_config_json"],
                encoded["kpi_summary_json"],
                encoded["detector_summary_json"],
                encoded["jenkins_build_ref"],
                encoded["started_at"],
                encoded["finished_at"],
                encoded["created_at"],
                encoded["updated_at"],
            ),
        )
        connection.commit()


def list_run_records() -> list[dict[str, Any]]:
    initialize_run_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT *
            FROM runs
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [_decode_record(dict(row)) for row in rows]


def get_run_record_by_id(run_id: str) -> dict[str, Any] | None:
    initialize_run_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT *
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

    return _decode_record(dict(row)) if row else None


def update_run_record(run_id: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    initialize_run_repository()
    filtered = {key: value for key, value in updates.items() if key in RUN_COLUMNS and key != "run_id"}
    if not filtered:
        return get_run_record_by_id(run_id)

    encoded = _encode_record(filtered, fill_defaults=False)
    assignments = ", ".join(f"{column} = ?" for column in encoded)
    values = [encoded[column] for column in encoded]
    values.append(run_id)

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.execute(
            f"""
            UPDATE runs
            SET {assignments}
            WHERE run_id = ?
            """,
            values,
        )
        connection.commit()

    return get_run_record_by_id(run_id)
