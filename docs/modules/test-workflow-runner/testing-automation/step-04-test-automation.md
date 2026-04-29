# Step 4 Test Automation

## 文档目标

这份文档记录 `Step 4：统一 result.json / timeline / artifact manifest 输出` 已落地和需要服务器确认的自动化测试内容。

Step 4 的测试目标不是验证真实 callback 是否已经上线，而是验证：

1. runner 产出的 `result.json` 有统一结果面。
2. `timeline` 和 `artifact_manifest` 结构稳定。
3. 这份结果已经具备被 Jenkins 归档、被 `platform-api` callback 消费的基础形状。

## 当前测试目标

围绕 Step 4，这一轮重点覆盖：

- `ResultBuilder` 顶层 `timeline`
- `ResultBuilder` 顶层 `artifact_manifest`
- CLI dry-run 结果形状

## 本轮已自动化场景

### 1. CLI dry-run 结果包含 timeline / artifact_manifest

对应测试：

- `test_cli_dry_run_writes_result_without_env_map`

### 2. ResultBuilder 能组装 timeline / artifact_manifest

对应测试：

- `test_result_builder_adds_timeline_and_artifact_manifest`

## 服务器验证命令

由用户在服务器执行：

```bash
cd /opt/jenkins_robotframework/test-workflow-runner
python -m pytest tests/test_orchestrator.py
python -m test_workflow_runner.cli configs/sample_request.json --dry-run --result-json artifacts/day2-step4-result.json
```

## 预期结果

- `artifacts/day2-step4-result.json` 顶层存在 `timeline`
- `artifacts/day2-step4-result.json` 顶层存在 `artifact_manifest`
- `artifact_manifest[0].kind = workflow_request_json`
- `artifact_manifest[1].kind = workflow_result_json`
- timeline 首尾分别为 `workflow_started` / `workflow_completed`

## Postman / SQLite 联动验证

Step 4 开始，已经值得做跨模块联调验证。

### 1. Postman 建议验证什么

建议复用现有资产：

- [platform-api-interview-practice.collection.json](../../../../platform-api/practice/postman/platform-api-interview-practice.collection.json)
- [platform-api-local.environment.json](../../../../platform-api/practice/postman/platform-api-local.environment.json)

最小联调顺序：

1. `POST /api/runs` 创建一条 `python_orchestrator` run
2. 用 Step 4 产出的 `artifact_manifest` 形状，手工拼一版 callback payload
3. `POST /api/runs/{run_id}/callbacks/jenkins`
4. `GET /api/runs/{run_id}` 和 `GET /api/runs/{run_id}/artifacts`

重点确认：

- `artifact_manifest` 能被接口正确接住
- 详情接口里 artifact 可见

### 2. SQLite 建议验证什么

建议复用现有 SQL 资产：

- [run-api-sql-drill.sql](../../../../platform-api/practice/sql/run-api-sql-drill.sql)

重点核对数据库字段：

- `status`
- `started_at`
- `finished_at`
- `artifact_manifest_json`

说明：

- `timeline` 当前仍然是执行层结果产物
- 现在不会作为独立 SQLite 列直接保存

## JMeter 位置说明

当前不是必须，但如果你要做最小 smoke，可以在 callback/detail 查询面稳定后补一轮：

- `POST /api/runs/{run_id}/callbacks/jenkins`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/artifacts`

建议只做轻量 smoke，不做重压。

可复用现有基础资产再扩：

- [platform-api-health-and-runs-smoke.jmx](../../../../platform-api/practice/jmeter/platform-api-health-and-runs-smoke.jmx)

## 当前结论

Step 4 是 `test-workflow-runner` 和 `platform-api` 开始发生稳定结果对接的第一步，所以从这一轮开始，Postman 和 SQLite 联动验证就有意义了。

## 相关文档

- [Step 4：统一 result.json / timeline / artifact manifest 输出](../steps/step-04-result-timeline-and-artifact-manifest.md)
- [模块总索引](../index.md)
