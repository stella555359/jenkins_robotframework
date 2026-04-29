from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from ..models import HandlerResult, KpiTestModelRequest, NormalizedUe, TestlineContext, TrafficItem
from ..taf_gateway import TafGateway


def utcnow_text() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()


@dataclass
class HandlerContext:
    request: KpiTestModelRequest
    testline_context: TestlineContext
    item: TrafficItem
    selected_ues: list[NormalizedUe]
    write_stdout: callable
    write_stderr: callable
    gateway: TafGateway


class BaseHandler:
    model_name = "base"
    result_bucket = "traffic"

    def build_success(self, context: HandlerContext, *, summary: dict, artifacts: list[dict] | None = None) -> HandlerResult:
        return HandlerResult(
            model=self.model_name,
            status="completed",
            started_at=utcnow_text(),
            completed_at=utcnow_text(),
            summary=summary,
            artifacts=artifacts or [],
            used_ues=[ue.ue_index for ue in context.selected_ues],
            params_echo=dict(context.item.params),
            stage_id=context.item.params.get("_stage_id"),
            item_id=context.item.item_id,
        )

    def build_failure(self, context: HandlerContext, *, error_message: str, summary: dict | None = None) -> HandlerResult:
        return HandlerResult(
            model=self.model_name,
            status="failed",
            started_at=utcnow_text(),
            completed_at=utcnow_text(),
            summary=summary or {},
            error_message=error_message,
            used_ues=[ue.ue_index for ue in context.selected_ues],
            params_echo=dict(context.item.params),
            stage_id=context.item.params.get("_stage_id"),
            item_id=context.item.item_id,
        )

    def execute_taf_action(self, context: HandlerContext, action_name: str, extra_summary: dict | None = None) -> HandlerResult:
        extra_summary = extra_summary or {}
        if context.request.runtime_options.dry_run:
            summary = {
                "implementation_mode": "dry_run",
                "action": action_name,
                "target_ue_labels": [ue.label for ue in context.selected_ues],
                **extra_summary,
            }
            context.write_stdout(f"[{action_name}] dry-run target_ues={len(context.selected_ues)}\n")
            return self.build_success(context, summary=summary)

        summary = context.gateway.execute(action_name, context)
        context.write_stdout(f"[{action_name}] completed target_ues={len(context.selected_ues)}\n")
        return self.build_success(
            context,
            summary={
                "implementation_mode": "taf_binding",
                "action": action_name,
                **summary,
            },
        )

    def execute_command(self, context: HandlerContext, action_name: str, command: list[str], *, cwd: str | None = None) -> HandlerResult:
        if context.request.runtime_options.dry_run:
            summary = {
                "implementation_mode": "dry_run",
                "action": action_name,
                "command": command,
                "cwd": cwd,
            }
            context.write_stdout(f"[{action_name}] dry-run command={' '.join(command)}\n")
            return self.build_success(context, summary=summary)

        completed = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            check=False,
            capture_output=True,
        )
        if completed.stdout:
            context.write_stdout(completed.stdout)
        if completed.stderr:
            context.write_stderr(completed.stderr)
        if completed.returncode != 0:
            return self.build_failure(
                context,
                error_message=f"{action_name} failed with exit code {completed.returncode}.",
                summary={"command": command, "cwd": cwd},
            )
        return self.build_success(
            context,
            summary={
                "implementation_mode": "subprocess",
                "action": action_name,
                "command": command,
                "cwd": cwd,
            },
            artifacts=[],
        )

    def resolve_command(self, raw_command: str) -> list[str]:
        parts = [part for part in str(raw_command or "").strip().split(" ") if part]
        if not parts:
            raise ValueError("command is required.")
        return parts

    def resolve_repository_path(self, context: HandlerContext, path_text: str | None) -> str | None:
        if not path_text:
            return None
        path = Path(path_text)
        if path.is_absolute():
            return str(path)
        repository_root = context.testline_context.repository_root
        if repository_root is None:
            return str(path)
        return str((repository_root / path).resolve())

    def resolve_working_directory(self, context: HandlerContext, path_text: str | None) -> str | None:
        if not path_text:
            repository_root = context.testline_context.repository_root
            return str(repository_root) if repository_root is not None else None
        path = Path(path_text)
        if path.is_absolute():
            return str(path)
        repository_root = context.testline_context.repository_root
        if repository_root is None:
            return str(path)
        path = repository_root / path
        return str(path)
