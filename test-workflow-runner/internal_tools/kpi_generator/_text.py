"""Text normalization, template parsing, progress logging."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any

from ._constants import (
    DEFAULT_TEST_LINE_PREFIX,
    ENVIRONMENT_CODE_PATTERN,
    ENVIRONMENT_TEST_LINE_MAP,
    PROGRESS_PREFIX,
    TEMPLATE_NAME_DELIMITER_PATTERN,
    TEMPLATE_NAME_LINEBREAK_PATTERN,
    TEMPLATE_NAME_MULTI_SPACE_PATTERN,
    TIMESTAMP_FORMAT,
)


def configure_logging(verbose: bool = False) -> logging.Logger:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="[kpi-generator] %(asctime)s %(levelname)s %(message)s",
    )
    return logging.getLogger("kpi_generator")


def sanitize_filename_token(value: str, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip()).strip("._-")
    return cleaned or fallback


def parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value.strip(), TIMESTAMP_FORMAT)


def normalize_dot_joined_token(value: str) -> str:
    parts = [re.sub(r"[^A-Za-z0-9-]+", "", part) for part in re.split(r"[._]+", str(value or "").strip())]
    normalized_parts = [part for part in parts if part]
    return ".".join(normalized_parts)


def normalize_build(value: str) -> str:
    return normalize_dot_joined_token(value)


def normalize_environment(value: str) -> str:
    return normalize_dot_joined_token(value)


def extract_environment_code(value: str) -> str:
    normalized_environment = normalize_environment(value)
    match = ENVIRONMENT_CODE_PATTERN.search(normalized_environment)
    if match:
        return match.group(2).upper()
    raise ValueError(
        "environment must contain a Txxx or Txxxx code, for example T813, T282, or T1234.CB0099.xxxx."
    )


def format_environment_filename_token(value: str) -> str:
    normalized_environment = normalize_environment(value)
    environment_code = extract_environment_code(normalized_environment)
    if normalized_environment.upper() == environment_code:
        return f"{environment_code}.SCF"
    return normalized_environment


def normalize_template_name(value: str) -> str:
    return str(value or "").strip()


def split_template_name_tokens(value: Any) -> list[str]:
    if isinstance(value, list):
        split_items: list[str] = []
        for item in value:
            split_items.extend(split_template_name_tokens(item))
        return split_items

    text = str(value or "").strip()
    if not text:
        return []

    if TEMPLATE_NAME_DELIMITER_PATTERN.search(text):
        return [part for part in TEMPLATE_NAME_DELIMITER_PATTERN.split(text) if part]
    if TEMPLATE_NAME_LINEBREAK_PATTERN.search(text):
        return [part for part in TEMPLATE_NAME_LINEBREAK_PATTERN.split(text) if part]
    if TEMPLATE_NAME_MULTI_SPACE_PATTERN.search(text):
        return [part for part in TEMPLATE_NAME_MULTI_SPACE_PATTERN.split(text) if part]
    return [text]


def parse_template_name_tokens(value: Any) -> list[str]:
    normalized_items: list[str] = []
    seen: set[str] = set()
    for item in split_template_name_tokens(value):
        normalized = normalize_template_name(item)
        lowered = normalized.lower()
        if not normalized or lowered in seen:
            continue
        seen.add(lowered)
        normalized_items.append(normalized)
    return normalized_items


def parse_dist_name_filter_tokens(value: Any) -> list[str]:
    normalized_items: list[str] = []
    seen: set[str] = set()
    for item in split_template_name_tokens(value):
        normalized = str(item or "").strip()
        lowered = normalized.lower()
        if not normalized or lowered in seen:
            continue
        seen.add(lowered)
        normalized_items.append(normalized)
    return normalized_items


def resolve_test_line(environment: str) -> str:
    environment_code = extract_environment_code(environment)
    if environment_code in ENVIRONMENT_TEST_LINE_MAP:
        return ENVIRONMENT_TEST_LINE_MAP[environment_code]
    if re.fullmatch(r"T\d{3,4}", environment_code):
        return f"{DEFAULT_TEST_LINE_PREFIX}{environment_code}"
    valid_examples = ", ".join(sorted(ENVIRONMENT_TEST_LINE_MAP))
    raise ValueError(
        f"environment must match Txxx or Txxxx format, for example T812 or T1234. Known mappings include: {valid_examples}."
    )


def emit_progress(stage: str, message: str, **extra: Any) -> None:
    event = {
        "stage": stage,
        "message": message,
        "timestamp": datetime.now().strftime(TIMESTAMP_FORMAT),
    }
    for key, value in extra.items():
        if value is not None:
            event[key] = value
    print(f"{PROGRESS_PREFIX}{json.dumps(event, ensure_ascii=False)}", flush=True)
