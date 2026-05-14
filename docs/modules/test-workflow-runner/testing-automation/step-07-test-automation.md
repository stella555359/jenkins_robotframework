# Step 7 Test Automation：Python KPI Runner MVP

## 已补充的自动化覆盖

- `test_ue_extractor_resolves_t813_capability_based_types`
  - 验证 `_android` 从 `qct_dx50` capability 推断为 `qct_dx50 / qualcomm`。
  - 验证 `_sigspark_1~_sigspark_2` 从 `pioneer` / `huawei_sigspark` capability 推断为 `pioneer / pioneer`。
- `test_request_loader_accepts_python_kpi_runner_models`
  - 验证 `prepare_ue`、`alarm_check`、`cell_lock` 等新 model 可通过 request validation。
  - 验证 `ue_scope.mode=ue_families` 可进入 request model。
- `test_request_loader_accepts_gnb_only_dry_run_without_selected_ues`
  - 验证不需要 UE 的 gNB WebUI 场景可以使用空 `selected_ues`。
  - 验证 `ru_reset` 可以通过 `repeat_count` 表达重复操作。
  - 验证 alarm/syslog 可以在 gNB-only 场景中作为 sidecar observation。
- `test_result_builder_adds_timeline_and_artifact_manifest`
  - 补充 `kpi_window` 输出断言。

## 服务器侧验证命令

```bash
cd /opt/jenkins_robotframework/test-workflow-runner
source .venv/bin/activate
python -m pytest tests/test_orchestrator.py
python -m test_workflow_runner.cli configs/sample_request.json --dry-run --result-json artifacts/python-kpi-runner-mvp-result.json
python -m test_workflow_runner.cli configs/sample_ue_kpi_request.json --dry-run --result-json artifacts/python-kpi-runner-ue-result.json
python -m test_workflow_runner.cli configs/sample_gnb_webui_request.json --dry-run --result-json artifacts/python-kpi-runner-gnb-webui-result.json
```

## 预期结果

- `pytest` 全部通过。
- CLI dry-run 生成 result JSON。
- result JSON 顶层包含 `kpi_window`。
- dry-run 日志中每个 item 会打印 `locks=...`，用于确认资源锁边界。
- gNB-only dry-run 的 `used_ues` 应为空数组。
- gNB-only dry-run 的 gNB 操作 summary 应包含 `repeat_count`。

## 常见失败模式

- 如果 pytest 在 `HandlerContext` 初始化处失败，通常是新增字段没有在 runner 中传入。
- 如果 `sample_request.json` 失败，先检查 `configs/env_map.json` 是否允许 `scripts/traffic`。
- 如果非 dry-run 失败并提示缺少 binding，先设置：

```bash
export GNB_KPI_TAF_BINDINGS_MODULE=test_workflow_runner.bindings.taf_power_ue
```

## 待真实设备验证

当前自动化主要覆盖 runner contract 和 dry-run 行为。真实设备侧还需要用户在 T813 环境确认：

- TAF/robotws Python callable 名称。
- `_android` 与 `_sigspark_*` 的真实 attach/detach 参数。
- traffic appserver / iperf 资源是否需要更细粒度锁。
