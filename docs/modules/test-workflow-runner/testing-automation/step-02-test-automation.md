# Step 2 Test Automation

## 文档目标

这份文档记录 `Step 2：stage / item engine 与并行安全边界` 已落地和需要服务器确认的自动化测试内容。

Step 2 的测试目标不是验证真实设备执行，而是验证：

1. runner 具备稳定的 stage / item 执行语义。
2. protected parallel stage 会在标准入口被拒绝。
3. 结果会稳定落入 preconditions / traffic / sidecars / followups 分桶。

## 当前测试目标

围绕 Step 2，这一轮重点覆盖：

- stage / item 最小执行链
- protected domain 并行拦截
- 结果分桶稳定性

## 本轮已自动化场景

### 1. protected parallel stage 被拒绝

对应测试：

- `test_request_loader_rejects_protected_parallel_stage`

### 2. stage / item dry-run 执行主路径成立

对应测试：

- `test_orchestrator_runner_executes_dry_run_workflow`

验证重点：

- `traffic_results` 数量
- `sidecar_results` 数量
- `status=completed`

## 服务器验证命令

由用户在服务器执行：

```bash
cd /opt/jenkins_robotframework/test-workflow-runner
python -m pytest tests/test_orchestrator.py
```

## 预期结果

- runner dry-run 测试通过。
- protected parallel stage 拒绝测试通过。
- 结果分桶断言通过。

## SQLite / Postman / JMeter 位置说明

### SQLite

当前不直接涉及。

Step 2 还是执行语义收口，还没有进入 callback 落库链路。

### Postman

当前不直接涉及。

Step 2 验证对象仍然是 runner 内部语义，不是外部 API。

### JMeter

当前不需要。

## 当前结论

Step 2 的自动化重点是冻结 workflow engine 的执行语义和安全边界。

## 相关文档

- [Step 2：实现 stage / item engine 与并行安全边界](../steps/step-02-stage-item-engine-and-safety-boundary.md)
- [模块总索引](../index.md)
