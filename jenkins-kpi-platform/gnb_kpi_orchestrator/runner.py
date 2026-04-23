from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Sequence

from .handlers import (
    ApplyPreconditionsHandler,
    AttachHandler,
    DetachHandler,
    DlTrafficHandler,
    HandoverHandler,
    KpiDetectorHandler,
    KpiGeneratorHandler,
    SwapHandler,
    SyslogCheckHandler,
    UlTrafficHandler,
)
from .handlers.base import HandlerContext, utcnow_text
from .models import HandlerResult, KpiTestModelRequest, NormalizedUe, OrchestratorState, TestlineContext, TrafficItem, TrafficStage
from .safety import validate_parallel_stage
from .taf_gateway import TafGateway


ProgressCallback = Callable[[str, str], None]
WriteCallback = Callable[[str], None]


class OrchestratorRunner:
    def __init__(self):
        self.handler_registry = {
            "apply_preconditions": ApplyPreconditionsHandler(),
            "attach": AttachHandler(),
            "handover": HandoverHandler(),
            "dl_traffic": DlTrafficHandler(),
            "ul_traffic": UlTrafficHandler(),
            "swap": SwapHandler(),
            "detach": DetachHandler(),
            "syslog_check": SyslogCheckHandler(),
            "kpi_generator": KpiGeneratorHandler(),
            "kpi_detector": KpiDetectorHandler(),
        }

    def execute(
        self,
        request: KpiTestModelRequest,
        context: TestlineContext,
        state: OrchestratorState,
        *,
        progress_callback: ProgressCallback | None = None,
        write_stdout: WriteCallback | None = None,
        write_stderr: WriteCallback | None = None,
    ) -> OrchestratorState:
        progress = progress_callback or (lambda stage, message: None)
        stdout = write_stdout or (lambda message: None)
        stderr = write_stderr or (lambda message: None)

        state.status = "running"
        state.kpi_test_starttime = utcnow_text()
        stages = request.traffic_stages()
        selected_ues_by_index = {ue.ue_index: ue for ue in self._selected_ues(request, context)}
        gateway = TafGateway(request.runtime_options.bindings_module)
        stdout(f"[runner] start env={request.env} stages={len(stages)} dry_run={request.runtime_options.dry_run}\n")

        for stage in stages:
            warnings = validate_parallel_stage(stage)
            state.validation_warnings.extend(warnings)

            enabled_items = [item for item in stage.items if item.enabled]
            if not enabled_items:
                continue
            progress("running_stage", f"Executing stage {stage.stage_id}: {stage.stage_name}")
            stdout(f"[runner] stage={stage.stage_id} mode={stage.execution_mode} items={len(enabled_items)}\n")
            results = self._execute_stage(
                request,
                context,
                stage,
                enabled_items,
                selected_ues_by_index,
                gateway=gateway,
                progress_callback=progress,
                write_stdout=stdout,
                write_stderr=stderr,
            )
            for result in results:
                self._append_result(state, result)
            if any(result.status == "failed" for result in results) and request.runtime_options.stop_on_failure:
                break

        all_results = [
            *state.precondition_results,
            *state.traffic_results,
            *state.sidecar_results,
            *state.followup_results,
        ]
        if any(result.status == "failed" for result in all_results):
            state.status = "failed"
            first_failure = next((item for item in all_results if item.status == "failed"), None)
            state.error_message = first_failure.error_message if first_failure else "Traffic execution failed."
        else:
            state.status = "completed"
        state.kpi_test_endtime = utcnow_text()
        stdout(f"[runner] end status={state.status}\n")
        return state

    def _execute_stage(
        self,
        request: KpiTestModelRequest,
        context: TestlineContext,
        stage: TrafficStage,
        items: Sequence[TrafficItem],
        selected_ues_by_index: dict[int, NormalizedUe],
        *,
        gateway: TafGateway,
        progress_callback: ProgressCallback,
        write_stdout: WriteCallback,
        write_stderr: WriteCallback,
    ) -> list[HandlerResult]:
        if stage.execution_mode == "parallel" and len(items) > 1:
            max_workers = min(request.runtime_options.max_parallel_workers, len(items))
            results: list[HandlerResult] = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(
                        self._execute_item,
                        request,
                        context,
                        stage,
                        item,
                        selected_ues_by_index,
                        gateway=gateway,
                        progress_callback=progress_callback,
                        write_stdout=write_stdout,
                        write_stderr=write_stderr,
                    ): item
                    for item in items
                }
                for future in as_completed(futures):
                    results.append(future.result())
            return sorted(results, key=lambda result: str(result.item_id))

        results = []
        for item in items:
            result = self._execute_item(
                request,
                context,
                stage,
                item,
                selected_ues_by_index,
                gateway=gateway,
                progress_callback=progress_callback,
                write_stdout=write_stdout,
                write_stderr=write_stderr,
            )
            results.append(result)
            if result.status == "failed" and request.runtime_options.stop_on_failure and not item.continue_on_failure:
                break
        return results

    def _execute_item(
        self,
        request: KpiTestModelRequest,
        context: TestlineContext,
        stage: TrafficStage,
        item: TrafficItem,
        selected_ues_by_index: dict[int, NormalizedUe],
        *,
        gateway: TafGateway,
        progress_callback: ProgressCallback,
        write_stdout: WriteCallback,
        write_stderr: WriteCallback,
    ) -> HandlerResult:
        handler = self.handler_registry[item.model]
        scoped_ues = self._resolve_item_ues(item, selected_ues_by_index)
        progress_callback("running_item", f"Executing {item.item_id} ({item.model})")
        write_stdout(f"[runner] item={item.item_id} model={item.model} ue_count={len(scoped_ues)}\n")

        context_item = TrafficItem(
            item_id=item.item_id,
            model=item.model,
            enabled=item.enabled,
            order=item.order,
            execution_mode=item.execution_mode,
            continue_on_failure=item.continue_on_failure,
            ue_scope=item.ue_scope,
            params={**item.params, "_stage_id": stage.stage_id},
        )
        try:
            return handler.run(
                HandlerContext(
                    request=request,
                    testline_context=context,
                    item=context_item,
                    selected_ues=scoped_ues,
                    write_stdout=write_stdout,
                    write_stderr=write_stderr,
                    gateway=gateway,
                )
            )
        except Exception as exc:
            write_stderr(f"[runner] item={item.item_id} failed: {exc}\n")
            return HandlerResult(
                model=item.model,
                status="failed",
                started_at=utcnow_text(),
                completed_at=utcnow_text(),
                summary={"implementation_mode": "runner_exception"},
                artifacts=[],
                error_message=str(exc),
                used_ues=[ue.ue_index for ue in scoped_ues],
                params_echo=dict(item.params),
                stage_id=stage.stage_id,
                item_id=item.item_id,
            )

    def _selected_ues(self, request: KpiTestModelRequest, context: TestlineContext) -> list[NormalizedUe]:
        requested_indexes = set(request.selected_ue_indexes())
        return [ue for ue in context.ues if ue.ue_index in requested_indexes]

    def _resolve_item_ues(self, item: TrafficItem, selected_ues_by_index: dict[int, NormalizedUe]) -> list[NormalizedUe]:
        if item.ue_scope.mode == "all_selected_ues":
            return list(selected_ues_by_index.values())
        if item.ue_scope.mode == "ue_indexes":
            return [selected_ues_by_index[index] for index in item.ue_scope.ue_indexes if index in selected_ues_by_index]
        if item.ue_scope.mode == "ue_types":
            return [ue for ue in selected_ues_by_index.values() if ue.ue_type in set(item.ue_scope.ue_types)]
        raise ValueError(f"Unsupported ue_scope.mode for runner: {item.ue_scope.mode}")

    def _append_result(self, state: OrchestratorState, result: HandlerResult) -> None:
        if result.model == "apply_preconditions":
            state.precondition_results.append(result)
            return
        if result.model == "syslog_check":
            state.sidecar_results.append(result)
            return
        if result.model in {"kpi_generator", "kpi_detector"}:
            state.followup_results.append(result)
            return
        state.traffic_results.append(result)
