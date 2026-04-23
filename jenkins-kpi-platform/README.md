# jenkins-kpi-platform

这里放 `Jenkins + Agent` 侧的执行编排资源。

当前已经补上的内容包括：

- `gnb_kpi_orchestrator/`
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
- 为 Jenkins pipeline 提供脚本入口

## 最短记忆版

```text
platform-api 负责收请求和聚合状态
jenkins-kpi-platform 负责真正执行 workflow
```
