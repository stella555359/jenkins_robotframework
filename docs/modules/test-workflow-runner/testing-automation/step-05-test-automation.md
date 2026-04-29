# Step 5 Test Automation

## 文档目标

这份文档记录 `Step 5：generator / detector internal API params contract` 已落地和需要服务器确认的自动化测试内容。

Step 5 的测试目标不是验证真实 Compass / detector 输出完全正确，而是验证：

1. followup handler 已切到 internal API 路径。
2. `environment / test_line` 的上下文注入行为稳定。
3. generator / detector 摘要已经具备被 callback 写回平台的基本形状。

## 当前测试目标

围绕 Step 5，这一轮重点覆盖：

- `kpi_generator` dry-run internal API 模式
- `kpi_detector` dry-run internal API 模式
- followup 结果分桶
- `environment / test_line` 默认补全

## 本轮已自动化场景

### 1. followup handler 走 internal API dry-run 路径

对应测试：

- `test_orchestrator_runner_supports_internal_followup_handlers_in_dry_run`

验证重点：

- `implementation_mode = internal_api_dry_run`
- 结果进入 `followup_results`
- `environment = T813`
- `test_line = 7_5_UTE5G402T813`

## 服务器验证命令

由用户在服务器执行：

```bash
cd /opt/jenkins_robotframework/test-workflow-runner
python -m pytest tests/test_orchestrator.py
python -m test_workflow_runner.cli configs/sample_request.json --dry-run --result-json artifacts/day2-step5-result.json
```

## 预期结果

- followup dry-run 通过。
- `followup_results` 中同时有 `kpi_generator` 和 `kpi_detector`。
- dry-run summary 中带 `environment / test_line`。

## Postman / SQLite 联动验证

Step 5 开始，已经可以和 `platform-api` 的 KPI 查询面做联调验证。

### 1. Postman 建议验证什么

建议复用现有资产：

- [platform-api-interview-practice.collection.json](../../../../platform-api/practice/postman/platform-api-interview-practice.collection.json)

最小联调顺序：

1. `POST /api/runs` 创建 `python_orchestrator` run
2. `POST /api/runs/{run_id}/callbacks/jenkins`，回写：
   - `artifact_manifest`
   - `kpi_summary`
   - `detector_summary`
3. `GET /api/runs/{run_id}`
4. `GET /api/runs/{run_id}/kpi`

重点确认：

- `kpi_summary` 可见
- `detector_summary` 可见
- `artifact_manifest` 同步可见

### 2. SQLite 建议验证什么

建议用现有 SQL drill 补数据库证据链：

- [run-api-sql-drill.sql](../../../../platform-api/practice/sql/run-api-sql-drill.sql)

重点核对：

- `kpi_summary_json`
- `detector_summary_json`
- `artifact_manifest_json`
- `status`

## JMeter 位置说明

如果你要引入最小性能验证，Step 5 比 Step 4 更适合，因为此时 `kpi` 查询面已经有明确语义。

建议只做轻量 smoke：

- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/kpi`

不要对 generator / detector 本体做重压；这一轮重点仍是结果查询面稳定，而不是性能压测。

## 当前结论

Step 5 是 `test-workflow-runner` 结果开始真正映射到平台 KPI / detector 查询面的那一步，所以 SQLite 和 Postman 联调从这里开始必须纳入 testing-automation 视野。

## 相关文档

- [Step 5：generator / detector internal API params contract](../steps/step-05-generator-detector-internal-api-contract.md)
- [模块总索引](../index.md)
