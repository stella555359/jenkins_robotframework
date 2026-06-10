# Insights Fusion AI Tool Workflow 调研记录

## 文档定位

这份文档记录公司内部 Insights Fusion 平台的 AI tool / workflow 能力，以及它和 `C:\TA\jenkins_robotframework` 项目的对接可行性。

当前调研目标：

```text
确认公司 AI workflow 平台是否能承接 jenkins_robotframework 的 AI-Driven Testing Platform 演进。
重点确认是否具备 Agent、Tool、MCP、知识库检索、认证和工作流编排能力。
```

## 已确认的页面能力

从 Workflow Builder 页面已经看到以下组件：

```text
Core:
  - Agent
  - Subworkflow
  - End Workflow

Tool:
  - Tool
  - Query SQL

Logic:
  - Condition
  - Loop
  - Human Input

Data:
  - Transform Data
  - Set State
```

当前判断：

```text
这不是普通聊天页面，而是一个低代码 AI Agent workflow 编排平台。
它具备 Agent 节点、Tool 节点、状态变量、人工确认和子 workflow 组合能力。
```

## 基本 workflow 结构

公司平台的常见 workflow 结构：

```text
Start
  -> Tool / Agent
  -> End Workflow
```

更适合当前测试平台的结构：

```text
Start
  -> Tool: get run detail
  -> Tool: get artifacts
  -> Tool: get Jenkins console
  -> Tool: search knowledge
  -> Agent: RCA and report
  -> Tool: save AI analysis
  -> End Workflow
```

## Workflow 变量机制

已知变量类型包括：

```text
Input Variables:
  workflow.*，由用户运行 workflow 时输入。
  示例：{{workflow.run_id}}

State Variables:
  state.*，workflow 执行过程中可读写。
  示例：{{state.count}}

Step Outputs:
  steps.*，前置 step 的输出。
  示例：{{steps.get_run_detail.output}}
```

这意味着可以把 Tool 输出交给 Agent，再把 Agent 输出交给后续 Tool 保存。

## Tool 选择页面观察

Tool 选择页面已经看到：

```text
External Integration:
  - Google Cloud Storage 文件类工具
  - propose_file_edit
  - glob_gcs_files
  - grep_gcs_files

Knowledge & Research:
  - acd_insights_agent
  - arch_insights_search_tool
  - troubleshooting_search_tool

Workflow Control:
  - get_access_token
```

当前判断：

```text
平台已经有内置工具、知识库检索工具和企业认证工具。
暂时没有直接看到 HTTP Request / REST API Tool。
```

## get_access_token 工具

`get_access_token` 的说明：

```text
Get the current user's Azure AD access token.
Returns a bearer token that can be used to authenticate with Azure-protected services
(MCP servers, Microsoft Graph, custom APIs).
The token is scoped to the user who started the workflow.
```

输出 schema：

```json
{
  "type": "object",
  "properties": {
    "access_token": {
      "type": "string",
      "description": "Azure AD bearer token"
    },
    "success": {
      "type": "boolean"
    }
  },
  "title": "get_access_token Response Schema"
}
```

当前判断：

```text
get_access_token 是认证工具，不是 API 调用工具。
它负责拿 Azure AD bearer token。
如果后续 platform-api 或 MCP Server 接入 Azure AD，就可以用这个 token 做认证。
```

典型用法：

```text
Tool: get_access_token
  -> output.access_token

后续 Tool / MCP Server:
  Authorization: Bearer {{steps.get_access_token.output.access_token}}
```

## MCP Server 支持

Start 节点右侧配置中已经看到：

```text
MCP Servers
  + Add
External tool servers available to agent and tool steps.
Steps reference servers by name.
```

点击 `Add MCP Server` 后，页面显示：

```text
Server Name
Server URL
Headers
Timeout
Test Connection
Add Server
```

Server URL 示例：

```text
https://mcp-server.example.com/sse
```

页面说明：

```text
SSE/HTTP endpoint.
Supports {{workflow.var}} templates.
```

当前判断：

```text
Insights Fusion 支持远程 MCP Server。
MCP transport 形态是 SSE / HTTP。
可以通过 Server URL 添加外部 tool server。
可以配置 headers。
可以 Test Connection。
```

这基本确认：

```text
jenkins_robotframework 可以通过自建 MCP Server 接入公司 AI workflow。
```

## 和 jenkins_robotframework 的推荐对接方式

推荐架构：

```text
Insights Fusion Workflow
  -> Agent node:
       使用公司内部 LLM 做分析、归类、报告生成

  -> Tool node:
       调用 jenkins_robotframework MCP Server 暴露的工具

jenkins_robotframework MCP Server
  -> 调 platform-api
  -> 调 Jenkins API
  -> 查 docs / knowledge base
  -> 保存 AI analysis result
```

## MCP Server 建议工具

第一版 POC 工具：

```text
get_health()
get_static_run_failure_example()
```

第一版真实集成工具：

```text
get_run_detail(run_id)
get_run_artifacts(run_id)
get_run_kpi(run_id)
get_run_progress(run_id)
save_ai_analysis_result(run_id, analysis)
```

第二版增强工具：

```text
get_jenkins_console(jenkins_build_ref)
build_ai_evidence(run_id)
search_project_knowledge(query)
search_failure_history(query)
generate_cursor_prompt(run_id)
```

后期受控执行工具：

```text
trigger_jenkins_run(run_id)
rerun_failed_case(run_id)
create_jira_draft(run_id)
```

注意：

```text
受控执行工具必须放在 Human Input 之后，不能让 Agent 自动直接执行。
```

## 推荐 workflow POC

Workflow 名称：

```text
AI Run Analysis POC
```

命令：

```text
/ai-run-analysis-poc
```

输入变量：

```text
run_id: string
```

推荐流程：

```text
Start
  input: run_id
  MCP Server: jenkins_robotframework

Tool: get_run_detail
  run_id = {{workflow.run_id}}

Tool: get_run_artifacts
  run_id = {{workflow.run_id}}

Tool: get_run_kpi
  run_id = {{workflow.run_id}}

Agent: ai_test_run_analysis_agent
  input:
    - {{steps.get_run_detail.output}}
    - {{steps.get_run_artifacts.output}}
    - {{steps.get_run_kpi.output}}

Tool: save_ai_analysis_result
  run_id = {{workflow.run_id}}
  analysis = {{steps.ai_test_run_analysis_agent.output}}

End Workflow
  output = {{steps.ai_test_run_analysis_agent.output}}
```

Agent prompt 草案：

```text
You are an AI testing triage assistant for a Jenkins + Robot Framework + KPI regression platform.

Analyze the provided run detail, artifacts and KPI summary.

Return the result in Chinese with:
1. one-line summary
2. failed stage
3. defect category
4. root cause hypothesis
5. evidence
6. confidence
7. recommended actions
8. markdown test report

Do not recommend changing environment or rerunning Jenkins without human confirmation.
```

## 当前可行性判断

已确认：

```text
Agent 节点存在。
Tool 节点存在。
知识库 / research 类工具存在。
get_access_token 可获取 Azure AD bearer token。
Start 节点支持添加远程 MCP Server。
MCP Server 支持 SSE / HTTP endpoint。
MCP Server 支持 Headers。
Workflow 支持 Human Input。
```

待确认：

```text
普通用户是否有权限添加自定义 MCP Server。
公司平台运行时能否访问我们部署的 MCP Server URL。
MCP Server 是否必须 HTTPS。
Headers 是否支持动态引用 get_access_token 输出。
MCP tools 是否能被 Tool 节点和 Agent 节点共同使用。
Agent 输出是否能作为后续 Tool 输入。
MCP Server 返回的大 JSON 是否有大小限制。
Workflow 是否支持保存 / 导出执行结果。
```

## 还需要从页面确认的点

建议继续在页面上确认：

```text
1. Add MCP Server 的 Headers 是否支持 {{steps.get_access_token.output.access_token}} 这种动态变量。
2. Test Connection 失败时是否显示详细错误，例如 DNS / TLS / 401 / timeout。
3. 添加 MCP Server 成功后，Tool 选择页面是否能看到该 server 暴露的 tools。
4. Tool 节点调用 MCP tool 后，输出 schema 是否可查看。
5. Agent prompt 中是否能引用 MCP tool 输出，例如 {{steps.get_run_detail.output}}。
6. Agent 输出是否能在后续 Tool body / argument 中引用。
7. Workflow run 历史里是否能查看每个 step 的 input / output。
8. 是否有 tool output size / timeout 限制。
9. 是否可以在 workflow 中使用 Human Input 做执行前确认。
10. 是否可以把 workflow export 成 JSON 方便版本管理。
```

## 需要问平台管理员的问题

如果页面上找不到答案，可以问管理员：

```text
1. 普通用户是否可以添加自定义 remote MCP server？
2. MCP Server 需要走 SSE 还是 streamable HTTP？是否只支持 /sse endpoint？
3. MCP Server 是否必须部署在公司内网或特定域名下？
4. 是否必须使用 HTTPS？
5. Headers 中是否支持 workflow / step output 动态变量？
6. 是否支持 Azure AD bearer token 访问 MCP Server？
7. Workflow runtime 的网络出口范围是什么？能访问哪些内网地址？
8. MCP tool 返回结果大小限制是多少？
9. Tool / Agent step 的执行超时是多少？
10. 是否支持把 workflow 发布给团队其他成员使用？
```

## 对本项目的结论

当前最推荐路线：

```text
公司 Insights Fusion：
  负责 LLM、Agent、workflow 编排、知识库检索和人机交互。

jenkins_robotframework：
  负责 MCP Server、测试平台数据、Jenkins artifact、KPI summary 和 AI 分析结果保存。
```

一句话：

```text
公司平台负责 AI 大脑和编排；
jenkins_robotframework 负责测试数据工具和结果落库。
```

这比项目自己直接接外部 OpenAI API 更符合公司环境和安全要求。
