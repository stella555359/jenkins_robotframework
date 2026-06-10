# Cursor + MCP 到 Insights Fusion AI RCA 演进方案

## 文档定位

这份文档记录 `C:\TA\jenkins_robotframework` 项目 AI RCA 能力的演进思路。

核心问题：

```text
先做 Cursor + MCP 版，让 Cursor/LLM 通过 MCP 查询 Jenkins / Robot / pytest / KPI evidence bundle 并生成 RCA。
后续是否能平滑升级为后台直接调用 LLM / Insights Fusion，独立生成 AI RCA、AI 测试报告、缺陷归类和知识库？
```

结论：

```text
可以。
前提是 Phase 1 设计时把 evidence collection 和 AI consumer 解耦。
```

也就是说，第一阶段不要把能力设计成 `Cursor 专用`，而是把核心能力设计成：

```text
标准 evidence bundle
  -> 可以被 Cursor MCP 读取
  -> 也可以被 platform-api / background worker 读取
  -> 也可以作为 Insights Fusion / LLM workflow 的输入
```

## 1. 背景理解

`test-auto-doc-mcp` 的模式已经证明：

```text
MCP server 本身不是 LLM。
MCP server 负责查询外部知识或系统数据。
Cursor / LLM 负责理解、总结、推理、生成代码或回答问题。
```

同样的模式可以应用到本项目：

```text
test-auto-doc MCP
  -> 查询 TAF / UTE 内部文档

jenkins_robotframework MCP
  -> 查询 Jenkins 日志、Robot 结果、pytest 结果、server 状态、artifact、KPI 输出
```

这样用户以后不用每次手动复制 Jenkins console log、pytest 输出或服务器命令结果给 Cursor，而是可以让 Cursor 通过 MCP 主动查询。

## 2. 两类能力要分开

### 2.1 MCP 能力

MCP 的定位是：

```text
被 Cursor / LLM 调用时，实时查询资料或系统状态。
```

它适合做：

- 查询 Jenkins build summary。
- 查询 Jenkins console log。
- 查询 Robot `log.html` / `report.html` / `output.xml` 位置。
- 查询 pytest result / Allure summary。
- 查询 KPI generator / detector 输出。
- 查询 artifact manifest。
- 查询某个 run 的 failure evidence bundle。

MCP 本身不负责持续后台监控，也不负责主动推送告警。

### 2.2 监控告警能力

自动监控和推送告警属于后台系统能力：

```text
Jenkins / pytest / Robot / server
  -> webhook / callback / scheduler
  -> evidence collector
  -> rule detector
  -> notification
```

它适合做：

- Jenkins build 完成后自动记录状态。
- build failed 后自动收集 console log 和 artifacts。
- 周期性检查 running build 是否超时。
- 检查 server service 是否异常。
- 推送 Teams / Email 告警。

如果要让告警本身带 AI 分析，则需要后台调用 LLM / Insights Fusion，而不是只依赖 Cursor MCP。

## 3. Phase 1：Cursor + MCP 版 AI RCA

目标：

```text
先证明 evidence bundle + Cursor/LLM AI RCA 是可行的。
```

推荐架构：

```text
Jenkins / Robot / pytest / KPI
  -> evidence collector
  -> evidence bundle JSON
  -> jenkins_robotframework MCP tools
  -> Cursor / LLM
  -> AI RCA / 测试报告 / 修复建议
```

典型使用方式：

```text
用户在 Cursor Chat 中问：
请分析 run_id=abc123 的失败原因，并生成 RCA 和下一步验证命令。

Cursor:
  -> 调用 get_failure_evidence_bundle(run_id="abc123")
  -> 调用 get_console_log(job_name, build_number)
  -> 调用 get_robot_artifacts(run_id)
  -> 调用 get_kpi_summary(run_id)
  -> 基于证据生成 RCA
```

这个阶段不需要项目自己接模型 API，因为 Cursor 已经提供 LLM 能力。

### 3.1 推荐 MCP tools

第一阶段可以只做只读 tools：

```text
get_latest_build_summary(job_name)
get_jenkins_build_log(job_name, build_number)
get_running_build_status(job_name)
get_run_artifact_manifest(run_id)
get_robot_result_summary(run_id)
get_pytest_result_summary(run_id)
get_kpi_summary(run_id)
get_failure_evidence_bundle(run_id)
```

最关键的是：

```text
get_failure_evidence_bundle(run_id)
```

因为它可以把多个系统里的证据收口成一份标准 JSON，减少 Cursor 多次来回查询。

### 3.2 Phase 1 的边界

Phase 1 先不做：

- 自动调用 LLM。
- 自动推送 AI RCA。
- 自动修改 Jenkins / server 配置。
- 写操作类 MCP tools，例如 restart service、delete artifact、rerun build。

Phase 1 只做：

- 自动收集证据。
- 标准化 evidence bundle。
- MCP 只读查询。
- Cursor/LLM 人工触发式 RCA。

## 4. 标准 Evidence Bundle

Phase 1 最重要的设计产物不是 MCP tool 本身，而是标准 evidence bundle。

建议结构：

```json
{
  "run_id": "abc123",
  "executor_type": "robot",
  "job_name": "robot-execution",
  "build_number": 128,
  "status": "failed",
  "failed_stage": "Robot Execution",
  "timestamps": {
    "started_at": "2026-05-25T10:00:00Z",
    "finished_at": "2026-05-25T10:18:00Z"
  },
  "environment": {
    "jenkins_url": "https://example/jenkins",
    "agent_label": "t813-agent",
    "testline": "TL813",
    "build": "gNB-build-id"
  },
  "console_log_excerpt": {
    "first_error": "keyword failed ...",
    "last_100_lines": "...",
    "matched_patterns": ["No such file", "Connection refused"]
  },
  "robot_summary": {
    "total": 10,
    "passed": 8,
    "failed": 2,
    "failed_cases": [
      {
        "name": "UE Attach",
        "error_message": "UE proxy unavailable",
        "failed_keyword": "Attach UE"
      }
    ]
  },
  "pytest_summary": {
    "total": 20,
    "passed": 19,
    "failed": 1
  },
  "kpi_summary": {
    "generator_status": "success",
    "detector_status": "failed",
    "anomalies": [
      {
        "metric": "attach_success_rate",
        "severity": "high",
        "message": "value below threshold"
      }
    ]
  },
  "artifacts": [
    {
      "type": "robot_log",
      "name": "log.html",
      "url": "..."
    },
    {
      "type": "robot_report",
      "name": "report.html",
      "url": "..."
    },
    {
      "type": "kpi_report",
      "name": "kpi.xlsx",
      "url": "..."
    }
  ],
  "failure_signature": {
    "category": "unknown",
    "stage": "Robot Execution",
    "primary_error": "UE proxy unavailable",
    "suspected_component": "taf.ue.proxy"
  }
}
```

这些字段后续可以被多个 consumer 复用。

## 5. Phase 2：独立 AI RCA / AI 测试报告

当 Phase 1 的 evidence bundle 稳定后，后续可以把 AI consumer 从 Cursor 扩展到后台服务。

推荐架构：

```text
Jenkins / Robot / pytest / KPI
  -> evidence collector
  -> evidence bundle JSON
  -> AI analysis service
  -> Insights Fusion / LLM API
  -> 保存 AI RCA / AI report
  -> portal / Teams / Email 展示
```

这时用户不一定需要打开 Cursor。

使用形态可以变成：

```text
automation-portal Run Detail
  [Generate AI Summary]
  [Generate RCA]
  [Generate Test Report]
```

或者：

```text
Jenkins failed
  -> 自动生成 AI RCA
  -> Teams 推送摘要
```

### 5.1 API 形态

可以新增后端接口：

```text
POST /api/runs/{run_id}/ai-analysis
GET  /api/runs/{run_id}/ai-analysis
GET  /api/runs/{run_id}/ai-report
```

这些接口内部同样调用：

```text
build_evidence_bundle(run_id)
```

也就是说 MCP 和 platform-api 共用同一份证据构建逻辑：

```text
MCP tool:
  get_failure_evidence_bundle(run_id)

API:
  POST /api/runs/{run_id}/ai-analysis

shared function:
  build_evidence_bundle(run_id)
```

这样后续升级不是重做，而是增加新的 AI consumer。

## 6. Phase 3：AI 缺陷归类和相似问题检索

当历史 evidence bundle、RCA、人工确认结论逐渐积累后，可以继续做：

```text
AI failure classification
similar failure search
historical RCA retrieval
```

典型流程：

```text
new failure evidence bundle
  -> 提取 failure signature
  -> 检索历史相似 failure
  -> 返回历史根因、修复方式、影响范围
  -> LLM 生成本次建议
```

可归类方向：

- 环境问题。
- Jenkins / pipeline 问题。
- Robot case / keyword 问题。
- TAF / UTE / UE proxy 问题。
- 产品功能问题。
- KPI 阈值异常。
- 测试数据或配置问题。

关键字段：

```text
failed_stage
primary_error
failed_case
failed_keyword
stacktrace
kpi_anomaly_type
suspected_component
environment
artifact_links
human_confirmed_root_cause
fix_action
```

## 7. Phase 4：AI 测试知识库和测试设计辅助

当历史缺陷、RCA 和修复记录形成稳定资产后，可以沉淀为测试知识库。

知识库内容：

- failure signature。
- root cause。
- fix action。
- verification command。
- affected component。
- related Robot case。
- related TAF / UTE library。
- related Jenkins job。
- related KPI metric。

后续用途：

```text
新需求 / 新测试场景
  -> AI 查询测试知识库
  -> 推荐已有 case、风险点、常见失败、验证命令
  -> 结合 test-auto-doc MCP 查询 TAF / UTE 内部文档
  -> 生成测试设计或 Robot / Python 自动化草稿
```

这样就从“失败后分析”扩展到“测试设计前预防”。

## 8. 使用形态对比

### 8.1 Cursor Chat 内使用

```text
用户问 Cursor
  -> Cursor 调 MCP 查 evidence
  -> Cursor LLM 生成 RCA / 报告 / 缺陷归类
```

优点：

- 最容易落地。
- 不需要自己接 LLM API。
- 适合开发者和平台维护者。

缺点：

- 需要人在 Cursor 里发起。
- 普通测试用户不一定会使用 Cursor。

### 8.2 Portal 页面中使用

```text
automation-portal
  -> 用户点击 Generate AI RCA
  -> platform-api 调用 Insights Fusion / LLM
  -> 保存并展示 AI 结果
```

优点：

- 普通用户可用。
- AI 结果可持久化。
- 更像产品功能。

缺点：

- 需要接入 LLM API 或 Insights Fusion。
- 需要权限、审计、成本和数据安全设计。

### 8.3 自动告警中使用

```text
Jenkins failed
  -> background worker 收集 evidence
  -> 调用 LLM / Insights Fusion
  -> Teams / Email 推送 AI RCA 摘要
```

优点：

- 最自动化。
- 用户不用主动查询。
- 适合值班、回归、CI 守护。

缺点：

- 需要后台任务和通知系统。
- 需要控制误报、超时、敏感信息和模型调用失败。

## 9. 推荐演进路线

最稳妥路线：

```text
Phase 1:
  evidence bundle + Cursor MCP + 人工触发 AI RCA

Phase 2:
  platform-api AI analysis endpoint + Insights Fusion / LLM API + portal 展示

Phase 3:
  historical failure classification + similar RCA search

Phase 4:
  AI testing knowledge base + 测试设计辅助
```

一句话总结：

```text
先让 AI 能稳定拿到证据，再让 AI 独立生成结论，最后让 AI 记住历史并反过来辅助测试设计。
```

## 10. 本轮学习记录

本轮解决的问题：

```text
明确 Cursor + MCP 版 AI RCA 与后续 Insights Fusion / LLM API 独立 AI 分析之间的关系。
确认 Phase 1 不是临时方案，而是后续 AI 缺陷归类、AI 测试报告、AI 测试知识库的基础。
```

关键设计原则：

```text
evidence collection 和 AI consumer 解耦。
```

核心调用链：

```text
Jenkins / Robot / pytest / KPI
  -> evidence collector
  -> evidence bundle JSON
  -> MCP tool 或 platform-api AI endpoint
  -> Cursor / Insights Fusion / LLM API
  -> RCA / report / classification / knowledge base
```

后续继续头脑风暴时优先回答：

1. `build_evidence_bundle(run_id)` 应放在哪个模块？
2. Phase 1 MCP server 是否独立成 `jenkins_robotframework_mcp`？
3. evidence bundle 第一版只支持 Jenkins build，还是同时支持 platform-api run？
4. Insights Fusion 第一版 workflow 输入字段应该和 evidence bundle 完全一致，还是做裁剪？
5. 哪些字段可能包含敏感信息，需要脱敏后再交给 LLM？
