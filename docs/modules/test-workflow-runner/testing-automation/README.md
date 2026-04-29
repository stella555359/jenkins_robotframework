# Test Workflow Runner Testing Automation

## 文档目标

这里记录 `test-workflow-runner` 模块每个 step 已落地和需要服务器确认的测试自动化内容。

和 `platform-api/testing-automation` 保持同一层级的记录方式：

- 每个 step 单独成文
- 区分“已写成 pytest / CLI 自动化”的内容
- 明确哪些 SQLite / Postman / JMeter 验证属于跨模块联调

## 当前目录

- [Step 1 Test Automation](step-01-test-automation.md)
- [Step 2 Test Automation](step-02-test-automation.md)
- [Step 3 Test Automation](step-03-test-automation.md)
- [Step 4 Test Automation](step-04-test-automation.md)
- [Step 5 Test Automation](step-05-test-automation.md)

## 当前约定

### 1. pytest / CLI

用于验证 runner 模块内部行为：

- request loader
- stage / item engine
- safety boundary
- runtime contract
- result builder
- followup handler

### 2. SQLite

不属于 runner 本地单元测试。

只在下面场景进入验证范围：

- runner 结果经 Jenkins callback 回写 `platform-api`
- 需要确认 `artifact_manifest_json / kpi_summary_json / detector_summary_json / status` 是否真实落库

### 3. Postman

不用于直接测试 runner CLI。

只在跨模块联调时使用，重点验证：

- `POST /api/runs`
- `POST /api/runs/{run_id}/callbacks/jenkins`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/artifacts`
- `GET /api/runs/{run_id}/kpi`

建议复用现有资产：

- [platform-api-interview-practice.collection.json](../../../../platform-api/practice/postman/platform-api-interview-practice.collection.json)
- [platform-api-local.environment.json](../../../../platform-api/practice/postman/platform-api-local.environment.json)

### 4. JMeter

只做最小 smoke，不做 runner 本体压测。

适合引入的时机：

- callback 链路稳定后
- detail / artifacts / kpi 查询面稳定后

建议复用现有基础资产：

- [platform-api-health-and-runs-smoke.jmx](../../../../platform-api/practice/jmeter/platform-api-health-and-runs-smoke.jmx)

## 当前结论

`test-workflow-runner` 的 testing-automation 现在分成两层：

1. 模块内：pytest + CLI
2. 跨模块：Postman + SQLite，必要时加 JMeter smoke
