# test-workflow-runner

这里放 `python_orchestrator` 执行器本体和 runner-specific 资源。

公共 Jenkins / Agent 集成层现在单独放在：

- `../jenkins-integration/`

当前已经补上的内容包括：

- `test_workflow_runner/`
  - GNB KPI workflow 的 Python orchestrator
- `tests/`
  - orchestrator 的最小单元测试

## 当前定位

这部分不是 Web 后端，也不是前端页面。

它负责的是：

- 在 Agent 上读取 workflow JSON
- 加载 `env_map.json` 和 testline configuration
- 执行 `attach / handover / dl_traffic / ul_traffic / swap / detach / syslog_check`
- 产出结果 JSON
- 为 Jenkins integration layer 提供 runner CLI 入口

它不负责：

- 通用 Jenkins Pipeline
- 通用 workspace / checkout / callback 组织
- `robot` 执行链的公共 bootstrap

## 最短记忆版

```text
platform-api 负责收请求和聚合状态
jenkins-integration 负责公共调度和桥接
test-workflow-runner 负责真正执行 workflow
```
