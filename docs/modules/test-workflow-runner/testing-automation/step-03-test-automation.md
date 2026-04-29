# Step 3 Test Automation

## 文档目标

这份文档记录 `Step 3：testline_configuration / robotws / TAF gateway 运行时契约` 已落地和需要服务器确认的自动化测试内容。

Step 3 的测试目标不是验证真实 TAF 是否执行成功，而是验证：

1. `repository_root` 已进入运行时上下文。
2. 相对 `script_path` 会被稳定解析成仓库绝对路径。
3. 默认 `cwd` 会回到仓库根目录，而不是依赖外部进程当前目录。

## 当前测试目标

围绕 Step 3，这一轮重点覆盖：

- 真实 context 与 dry-run context 的仓库根目录语义
- `dl_traffic / ul_traffic` 的相对脚本解析
- 默认 `working_directory` 语义

## 本轮已自动化场景

### 1. dry-run 结果中的 script_path 会绝对化

对应测试：

- `test_orchestrator_runner_executes_dry_run_workflow`
- `test_cli_dry_run_context_uses_repository_root_for_relative_script_paths`

### 2. 默认 cwd 会回到 repository_root

对应测试：

- `test_orchestrator_runner_executes_dry_run_workflow`
- `test_cli_dry_run_context_uses_repository_root_for_relative_script_paths`

## 服务器验证命令

由用户在服务器执行：

```bash
cd /opt/jenkins_robotframework/test-workflow-runner
python -m pytest tests/test_orchestrator.py
python -m test_workflow_runner.cli configs/sample_request.json --dry-run --result-json artifacts/day2-step3-result.json
```

## 预期结果

- `dl_traffic.summary.command[1]` 为仓库绝对路径。
- `ul_traffic.summary.command[1]` 为仓库绝对路径。
- `summary.cwd` 等于仓库根目录。

## SQLite / Postman / JMeter 位置说明

### SQLite

当前不直接落库。

但 Step 3 是后续 `runner result -> Jenkins callback -> SQLite` 的前提，因为脚本和工作目录如果不稳定，后续结果链路也不稳定。

### Postman

当前不直接使用 Postman 验证 runner。

等 Step 4/5 的结果输出形状稳定后，建议用现有 Postman 资产验证 callback 对 `platform-api` 的映射：

- [platform-api-interview-practice.collection.json](../../../../platform-api/practice/postman/platform-api-interview-practice.collection.json)

### JMeter

当前不需要。

## 当前结论

Step 3 的自动化重点是把“真实运行时路径语义”固定下来，为后续 Jenkins/UTE 集成做准备。

## 相关文档

- [Step 3：接入 testline_configuration / robotws / TAF gateway 的运行时契约](../steps/step-03-testline-robotws-taf-gateway-runtime-contract.md)
- [模块总索引](../index.md)
