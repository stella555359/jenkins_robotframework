# Step 1 Test Automation

## 文档目标

这份文档记录 `Step 1：runner request loader / workflow schema / CLI dry-run` 已落地和需要服务器确认的自动化测试内容。

Step 1 的测试目标不是验证真实 Jenkins/UTE/TAF，而是验证：

1. workflow request 能被稳定加载。
2. schema 和 safety 校验能在标准入口挡住不安全请求。
3. CLI `--dry-run` 能在不依赖真实 testline 配置时写出最小 `result.json`。

## 当前测试目标

围绕 Step 1，这一轮重点覆盖：

- request loader 主路径
- protected parallel stage 拒绝路径
- runner dry-run 最小执行链
- CLI dry-run 结果文件写出

## 本轮已自动化场景

### 1. 合法 request 能被加载

对应测试：

- `test_request_loader_accepts_valid_payload`

### 2. 不安全并行 stage 被标准入口拒绝

对应测试：

- `test_request_loader_rejects_protected_parallel_stage`

### 3. dry-run workflow 能跑通

对应测试：

- `test_orchestrator_runner_executes_dry_run_workflow`

### 4. CLI dry-run 能写出 result.json

对应测试：

- `test_cli_dry_run_writes_result_without_env_map`

## 服务器验证命令

由用户在服务器执行：

```bash
cd /opt/jenkins_robotframework/test-workflow-runner
python -m pytest tests/test_orchestrator.py
python -m pytest tests/test_orchestrator.py --alluredir=allure-results
python -m test_workflow_runner.cli configs/sample_request.json --dry-run --result-json artifacts/day2-step1-result.json
```

## 预期结果

- 与 Step 1 相关 pytest 通过。
- `artifacts/day2-step1-result.json` 可生成。
- `status=completed`。
- `testline=testline` 完整名，`testline_alias=T813`。

## SQLite / Postman / JMeter 位置说明

### SQLite

当前不直接涉及。

原因：

- Step 1 只验证 runner 本地入口和 dry-run。
- 还没有进入 `platform-api callback -> SQLite` 这条集成链。

### Postman

当前不直接涉及。

原因：

- runner 这一轮仍是 CLI 入口，不是 HTTP API。

### JMeter

当前不需要。

原因：

- Step 1 不涉及接口吞吐或 callback 查询压力。

## 当前结论

Step 1 的自动化重点是把执行层入口固定下来，而不是做跨模块联调。

## 相关文档

- [Step 1：runner request loader / workflow schema / CLI dry-run](../steps/step-01-runner-request-loader-and-cli.md)
- [模块总索引](../index.md)
