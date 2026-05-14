# Step 7：Python KPI Runner MVP

## 这一步解决的问题

这一轮把 `test-workflow-runner` 从“通用 dry-run 执行骨架”推进到“纯 Python KPI 测试编排 MVP”：

- 从真实 `testline_configuration` module globals 中识别 T813 的 `_android`、`_sigspark_*` UE 对象名。
- 通过 `capabilities` 推断 `ue_type` 和 `ue_family`，例如 `_android -> qct_dx50 / qualcomm`，`_sigspark_* -> pioneer / pioneer`。
- 支持 `prepare_ue`、`attach`、`detach`、UL/DL traffic、gNB control、alarm/syslog observation、KPI followup。
- 支持先不接真实设备的 dry-run 主线：
  - 场景 1：需要 UE 的 `prepare_ue -> attach -> optional traffic/mobility -> detach -> KPI followup`。
  - 场景 2：不需要 UE 的 gNB WebUI 操作 `site_reset / ru_reset / cell_lock_unlock`，重复执行后检查 alarm/syslog。
- 为 UE、gNB、cell、appserver、KPI followup 增加 runner 内 resource lock，避免 parallel stage 内抢同一资源。
- 输出统一 `kpi_window`，让 `kpi_generator` 默认使用业务窗口。

## 改了哪些文件

- `test-workflow-runner/test_workflow_runner/ue_extractor.py`
  - 增加 capability-based UE type/family 推断和 object name label fallback。
- `test-workflow-runner/test_workflow_runner/models.py`
  - 扩展支持的 model、`NormalizedUe` 字段、`UeScope.ue_families`、业务窗口字段。
- `test-workflow-runner/test_workflow_runner/request_loader.py`
  - 增加新 model、UE family scope、gNB control、alarm/syslog window 校验。
  - 允许 gNB-only request 使用空 `selected_ues` 和 `ue_scope.mode=none`。
- `test-workflow-runner/test_workflow_runner/runner.py`
  - 注册新 handler，增加 resource lock，识别 followup 前业务窗口。
- `test-workflow-runner/test_workflow_runner/handlers/`
  - 增加 `prepare_ue`、gNB control、`alarm_check`，增强 attach/detach/traffic/syslog 参数。
  - 增加 `ru_reset`、`cell_lock_unlock` dry-run 表达。
- `test-workflow-runner/test_workflow_runner/bindings/taf_power_ue.py`
  - 提供可注入的 Python TAF binding skeleton。
- `test-workflow-runner/test_workflow_runner/result_builder.py`
  - 输出 `kpi_window`。
- `test-workflow-runner/configs/sample_request.json`
  - 更新为 Python KPI Runner request 示例。
- `test-workflow-runner/configs/sample_ue_kpi_request.json`
  - 增加需要 UE 的 dry-run MVP 请求示例。
- `test-workflow-runner/configs/sample_gnb_webui_request.json`
  - 增加不需要 UE 的 gNB WebUI dry-run 请求示例。
- `test-workflow-runner/configs/env_map.example.json`
  - 增加外部 `testline_configuration` / `robotws` 路径示例。
- `test-workflow-runner/tests/test_orchestrator.py`
  - 增加 UE capability 推断、新 request model、KPI window 测试覆盖。

## 核心调用链

```text
RequestLoader
  -> EnvConfigResolver.load_testline_context
  -> UeExtractor.extract(tl, module_globals=vars(module))
  -> OrchestratorRunner.execute
  -> resource_keys_for_item + per-run Lock
  -> Handler.run
  -> TafGateway.execute(run_<action>)
  -> ResultBuilder.build_success(kpi_window + timeline + artifact_manifest)
```

## 关键字段

- `NormalizedUe.label`
  - 优先来自 UE 对象自身 `label`，否则使用 module globals 中的变量名，例如 `_android`。
- `NormalizedUe.ue_type`
  - 优先显式 `ue_type`，否则从 `capabilities` 推断。
- `NormalizedUe.ue_family`
  - 用于业务分组，例如 `pioneer` family 可覆盖 `_sigspark_1~_sigspark_6`。
- `UeScope.mode=ue_families`
  - 支持按 UE family 选择 item 目标 UE。
- `params._resource_keys`
  - runner 注入的资源锁 key，只在内部流转。
- `kpi_window.business_start_time / business_end_time`
  - KPI followup 默认使用的业务窗口。

## 服务器验证命令

按项目约定，这些命令由用户在目标服务器执行，AI 不主动执行：

```bash
cd /opt/jenkins_robotframework/test-workflow-runner
source .venv/bin/activate
python -m pytest tests/test_orchestrator.py
python -m test_workflow_runner.cli configs/sample_request.json --dry-run --result-json artifacts/python-kpi-runner-mvp-result.json
python -m test_workflow_runner.cli configs/sample_ue_kpi_request.json --dry-run --result-json artifacts/python-kpi-runner-ue-result.json
python -m test_workflow_runner.cli configs/sample_gnb_webui_request.json --dry-run --result-json artifacts/python-kpi-runner-gnb-webui-result.json
```

## 预期结果

- `pytest` 通过。
- CLI 返回 exit code `0`。
- `artifacts/python-kpi-runner-mvp-result.json` 中：
  - `status` 为 `completed`。
  - `resolved_config.config_id` 为 `T813`。
  - `summary.validation_warnings` 为空或只包含明确可解释的并行安全提示。
  - `results.traffic` 中包含 `prepare_ue`、`attach`、`dl_traffic`、`ul_traffic`、`detach`。
  - `results.sidecars` 中包含 `alarm_check`、`syslog_check`。
  - 顶层存在 `kpi_window.business_start_time` 和 `kpi_window.business_end_time`。
- `artifacts/python-kpi-runner-gnb-webui-result.json` 中：
  - `results.traffic[0].model` 为 `ru_reset` 或所选 gNB 操作。
  - `results.traffic[0].used_ues` 为空数组。
  - `results.traffic[0].summary.repeat_count` 等于 request 中的重复次数。
  - `results.sidecars` 包含 `alarm_check` 和 `syslog_check`。

## 常见失败判断

- `Only these traffic models are supported`
  - 说明 request 中的 `model` 没有注册到 `SUPPORTED_TRAFFIC_MODELS` 或 handler registry。
- `cell_id is required`
  - `cell_lock/cell_unlock` 缺少 `params.cell_id` 或 `params.cell_name`。
- `window_source must be workflow, stage, or custom`
  - alarm/syslog window 参数非法。
- `No TAF bindings module configured`
  - 非 dry-run 时没有设置 `runtime_options.bindings_module` 或 `GNB_KPI_TAF_BINDINGS_MODULE`。
- `does not expose a callable for action`
  - 当前真实 TAF/robotws 对象没有对应 Python callable，需要在 `bindings/taf_power_ue.py` 中对接真实 API。

## 需要用户确认的业务点

- `_sigspark_*` 当前统一归为 `pioneer` family，这符合当前 MVP 视角；如果后续要区分 `pioneer` 和 `huawei_sigspark`，可以在 binding 层继续细分。
- `site_reset/rf_reset` 默认只允许 serial stage，避免和 UE traffic / attach 并发抢 gNB。
- `kpi_generator` 未显式传 `report_timestamps_list` 时，默认使用 runner 记录的业务窗口。

## 小结和复盘问题

这一步没有把 Robot keyword 逐行翻译成 Python，而是让 runner 负责编排、窗口和资源边界，让真实设备动作通过 Python binding 注入。

复盘问题：

- 当前测试线上的 `_sigspark_2~_sigspark_6` 是否都应该使用同一类 attach/detach adapter？
- 真实 TAF 对象里 prepare/attach/detach 的 Python callable 名称是什么？
- gNB control 是否需要进一步细化到 `gnb:<id>` 与 `cell:<id>` 的组合锁？
