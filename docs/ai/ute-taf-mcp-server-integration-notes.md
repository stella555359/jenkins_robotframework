# UTE TAF MCP Server 与 jenkins_robotframework 项目结合分析

## 文档定位

这份文档记录 UTE TAF MCP Server（`test-auto-doc-mcp`）与 `C:\TA\jenkins_robotframework` 项目的结合思路。

它用于 Cursor 重启后的上下文恢复，避免忘记当前判断：

```text
UTE TAF MCP Server 主要服务 Cursor 本地开发阶段，
用于查询 UTE TAF 内部 API、UEVT、测试规范和相关文档，
从而减少 AI 生成测试代码 / 测试设计时的幻觉。
```

它和前面讨论的 Insights Fusion MCP Server 不是同一个使用场景。

## 背景信息

内部通知主题：

```text
UTE TAF MCP server is now available!
```

核心内容：

```text
You can now use the UTE TAF MCP Server distributed with test-auto-doc-mcp package,
with access to internal APIs and the full documentation of the UTE TAF team.
```

它带来的能力：

```text
writing test cases without hallucinations
asking questions about internal APIs and the entire UTE TAF team, including UEVT
exploring internal TAF / UTE testing documentation from Cursor
```

## 安装与 Cursor 接入方式

### 安装

```bash
pipx install test-auto-doc-mcp
```

如果没有 `pipx`：

```bash
pip install pipx
```

### stdio 模式

`stdio` 是默认模式，推荐给本地 Cursor 使用。

Cursor MCP 配置示例：

```json
{
  "mcpServers": {
    "test-auto-doc": {
      "command": "test-auto-doc"
    }
  }
}
```

含义：

```text
Cursor 启动时自动运行 test-auto-doc 命令。
Cursor 通过本地标准输入 / 输出和 MCP server 通信。
```

适合：

```text
个人本地开发
Cursor 中查询 UTE TAF API
Cursor 中生成测试用例草案
```

### streamable-http 模式

适合远程或共享部署。

启动：

```bash
test-auto-doc --transport streamable-http
```

Cursor 配置：

```json
{
  "mcpServers": {
    "test-auto-doc": {
      "url": "http://localhost:8050/mcp"
    }
  }
}
```

### 覆盖 Knowledge Base API URL

```bash
test-auto-doc --api-url http://localhost:8000
```

含义：

```text
让 MCP server 连接指定的 Knowledge Base API。
可用于本地开发或测试环境。
```

## 和 Insights Fusion MCP 的区别

### UTE TAF MCP Server

主要用于：

```text
Cursor 本地开发阶段
```

调用链：

```text
Cursor
  -> test-auto-doc MCP Server
  -> UTE TAF docs / internal APIs / UEVT knowledge
  -> Cursor 生成更准确的测试代码和测试设计
```

适合场景：

```text
查询 UTE TAF 内部 API
理解 UEVT
生成 Robot / TAF 测试用例草案
生成 workflow_spec 草案
检查测试代码是否符合内部规范
减少 Cursor 对内部 API 的幻觉
```

### Insights Fusion MCP Server

主要用于：

```text
公司 AI Workflow Builder 运行时
```

调用链：

```text
Insights Fusion Workflow
  -> remote MCP Server
  -> jenkins_robotframework platform-api / Jenkins / artifacts
  -> Agent 分析日志、RCA、测试报告
```

适合场景：

```text
AI 日志分析
AI 缺陷归类
AI RCA
AI 测试报告
AI agent 调 Jenkins / 查运行结果
```

## 对 jenkins_robotframework 的价值

UTE TAF MCP Server 对当前项目最有价值的是：

```text
AI 自动生成测试用例
AI 生成 workflow_spec
AI 理解 TAF / robotws / UEVT API
AI 分析测试代码是否符合内部规范
AI 帮助补齐真实 UTE Robot / TAF 调用方式
```

它不主要解决：

```text
自动分析 Jenkins run
自动读取 KPI runner artifacts
自动保存 AI analysis result
自动调度 Jenkins
```

这些更适合由 `jenkins_robotframework` 自己提供 MCP Server 或 platform-api 接口，并由 Insights Fusion workflow 调用。

## 和 AI-Driven Testing Platform 六个方向的关系

### 1. AI 自动生成测试用例

强相关。

原因：

```text
Cursor 可以通过 UTE TAF MCP Server 查询内部 API 和测试规范，
再生成更靠谱的测试用例草案。
```

推荐方式：

```text
需求 / feature 描述
  -> Cursor + UTE TAF MCP 查询内部 API
  -> 生成自然语言测试用例
  -> 生成 workflow_spec 草案
  -> 人工 review
  -> 进入 Jenkins 执行
```

### 2. AI 日志分析

弱相关。

日志分析主要依赖：

```text
Jenkins console
Robot output.xml
runner result JSON
历史缺陷库
项目排障记录
```

UTE TAF MCP 可以补充 TAF / UEVT 背景知识，但不是主数据源。

### 3. AI 缺陷归类

中等相关。

如果失败和 TAF API / UEVT / Robot 调用方式有关，UTE TAF MCP 可以辅助解释。

例如：

```text
TAF API 参数错误
UEVT 调用方式错误
Robot keyword 使用不符合规范
```

### 4. AI 测试报告

间接相关。

它可以帮助报告中的技术解释更准确，但报告主证据仍应来自：

```text
Jenkins artifacts
runner result
KPI summary
detector summary
```

### 5. AI 测试知识库

强相关。

UTE TAF MCP Server 本身就是一个内部测试知识入口。

它可以作为：

```text
Cursor 开发时的知识源
测试用例生成时的 API 依据
内部 TAF / UEVT 文档查询入口
```

### 6. AI Agent 自动调度

弱相关。

UTE TAF MCP 不主要负责调 Jenkins / GitLab / DB / platform-api。

自动调度更适合：

```text
Insights Fusion workflow
jenkins_robotframework MCP Server
platform-api
Jenkins API
```

## 推荐项目定位

建议把 UTE TAF MCP Server 放在 AI 平台演进中的这个位置：

```text
开发前 / 设计阶段：
  Cursor + UTE TAF MCP
  -> 生成测试设计、测试用例草案、workflow_spec 草案

运行中：
  Jenkins + Robot / test-workflow-runner
  -> 执行测试

运行后：
  Insights Fusion + jenkins_robotframework MCP / platform-api
  -> 日志分析、RCA、测试报告
```

整体链路：

```text
Requirement / Feature
  -> Cursor + UTE TAF MCP
  -> Test case draft / workflow_spec draft
  -> Human review
  -> platform-api / Jenkins
  -> Robot / KPI runner
  -> artifacts / results
  -> AI RCA / report
```

## 建议 Cursor 使用方式

配置好 UTE TAF MCP Server 后，可以在 Cursor 中这样提问：

```text
请基于 UTE TAF API 和 UEVT 文档，帮我生成一个 UE attach + DL traffic + KPI check 的测试设计草案。
```

```text
请查询 UTE TAF 中与 UE attach、traffic、handover 相关的 API，并说明它们适合如何映射到 test-workflow-runner 的 workflow item。
```

```text
请基于当前 workflow_spec schema，生成一个适合 T813 testline 的 dry-run workflow_spec 草案，并标出哪些字段需要人工确认。
```

```text
请检查这个 Robot / TAF 调用草案是否可能使用了不存在的内部 API。
```

## 需要配置 rules / skills

内部通知提醒：

```text
Remember to setup proper rules and skills that will support Cursor to use the MCP server right.
```

建议后续补充：

```text
.cursor/rules/ute-taf-mcp-usage.mdc
```

规则目标：

```text
当生成 UTE / TAF / UEVT / Robot 相关测试代码时，
优先通过 test-auto-doc MCP 查询内部 API 和文档，
不要凭空猜测内部函数、参数或 keyword。
```

## 和当前 docs/ai 其他文档的关系

相关文档：

```text
docs/ai/ai-driven-intelligent-testing-platform-brainstorm.md
docs/ai/insights-fusion-ai-tool-workflow-notes.md
docs/overview/ai-driven-intelligent-testing-platform.md
docs/modules/jenkins-integration/guides/ai-evidence-collection.md
docs/modules/platform-api/steps/step-16-ai-analysis-contract.md
docs/modules/automation-portal/steps/step-02-ai-run-detail-experience.md
```

分工：

```text
ai-driven-intelligent-testing-platform-brainstorm.md:
  总体 AI 化头脑风暴。

insights-fusion-ai-tool-workflow-notes.md:
  公司 AI workflow / MCP 接入运行时分析。

ute-taf-mcp-server-integration-notes.md:
  Cursor + UTE TAF MCP 在测试设计和用例生成阶段的作用。
```

## 重启后下一步

Cursor 重启后，建议先恢复：

```text
1. 确认是否已经安装 pipx。
2. 安装 test-auto-doc-mcp。
3. 配置 Cursor MCP：
   ~/.cursor/mcp.json
4. 重启 Cursor。
5. 用一个简单问题验证 UTE TAF MCP 是否可用。
6. 再尝试让 Cursor 基于 UTE TAF MCP 生成一个 workflow_spec 草案。
```

验证问题示例：

```text
请查询 UTE TAF / UEVT 中与 UE attach 相关的内部 API 或文档，并总结适合自动化测试用例设计的要点。
```

如果 MCP 可用，预期：

```text
Cursor 不再只凭通用知识回答，
而是能引用或利用 UTE TAF 内部文档 / API 信息。
```

## 当前结论

一句话：

```text
UTE TAF MCP Server 是给 Cursor 用的内部测试知识和 API 查询工具，
它适合支撑 AI 自动生成测试用例和 workflow_spec 草案；
而 Jenkins run 分析、RCA、测试报告和自动调度，则更适合由 Insights Fusion workflow + jenkins_robotframework MCP Server 承接。
```
