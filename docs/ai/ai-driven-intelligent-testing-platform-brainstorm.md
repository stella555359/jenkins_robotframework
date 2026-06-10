# AI-Driven Intelligent Testing Platform 头脑风暴记录

## 文档定位

这份文档用于记录 `C:\TA\jenkins_robotframework` 项目 AI 化演进的头脑风暴分析。

当前讨论目标不是马上定最终技术方案，而是先判断下面这些方向：

```text
1. 是否适合结合当前 Jenkins KPI 自动化测试平台落地
2. 每个方向大概怎么实现
3. 哪些适合先做 MVP
4. 哪些需要后置，并加人工确认和安全边界
```

当前结论：

```text
整体可行。

这个项目已经具备 Jenkins、Robot/KPI runner、artifact、callback、platform-api、automation-portal，
这些正好是 AI 测试平台所需的执行证据、运行记录和操作入口。
```

## 总体可行性判断

可以把 AI 化方向分成三类：

```text
第一类：现在最适合先做
- AI 日志分析
- AI 缺陷归类
- AI 测试报告
- AI 测试知识库

第二类：可以做，但需要人工确认
- AI 自动生成测试用例

第三类：可以做，但必须最后做，且要强安全控制
- AI agent 自动调度 Jenkins / GitLab / DB / 测试平台 / 接口
```

原因：

```text
分析类 AI 风险低，价值明显。
生成类 AI 需要人工 review。
自动执行类 AI 权限风险最高，必须在平台稳定后做。
```

## 方向一：AI 自动生成测试用例

### 可行性

可行，但不建议一开始就让 AI 直接生成可执行 Robot case 并提交运行。

更稳的实现方式：

```text
需求文档 / feature 描述
  -> LLM 提取测试点
  -> 生成测试场景
  -> 生成测试用例草案
  -> 映射到已有 Robot case / workflow model
  -> 人工确认
  -> 再进入 Jenkins 执行
```

### 结合本项目的输出形式

可以有两种输出：

```text
输出 A：自然语言测试用例
  - 前置条件
  - 测试步骤
  - 预期结果
  - 优先级
  - 测试数据

输出 B：workflow_spec 草案
  - attach
  - dl_traffic
  - ul_traffic
  - kpi_generator
  - kpi_detector
```

短期更建议先生成 `workflow_spec` 草案。

原因：

```text
当前项目已经有 WorkflowSpec、WorkflowBuilder 和 test-workflow-runner。
workflow_spec 是结构化输入，比直接生成 .robot 文件更容易校验和落地。
```

不建议初期直接生成 `.robot` 文件：

```text
Robot case 依赖 robotws、变量、testline、TAF、环境知识。
AI 容易生成看起来合理但实际跑不通的 case。
```

## 方向二：AI 日志分析

### 可行性

非常可行，而且是最适合优先做的方向。

推荐链路：

```text
Jenkins console / Robot log / runner result
  -> 日志清洗
  -> 错误片段提取
  -> error signature 规则提取
  -> embedding
  -> 检索历史缺陷 / FAQ / Jenkins 经验
  -> LLM 总结
  -> 输出根因候选和建议动作
```

### 为什么要先做规则前处理

不要一开始就把完整日志直接丢给 LLM。

更稳定的流程：

```text
日志
  -> 规则提取 failed stage / error signature
  -> embedding 检索历史相似问题
  -> LLM 结合证据总结
```

因为 Jenkins / Robot 错误有很多确定性模式：

```text
No such file or directory
Permission denied
ModuleNotFoundError
No route to host
Waiting for next available executor
script returned exit code
Robot Framework test failed
```

这些可以先用规则提取，不需要 LLM 猜。

### 本项目可用证据源

```text
Jenkins console
artifacts/python-kpi-runner-result.json
artifacts/source-checkout.json
artifacts/python-env.json
Robot output.xml
KPI detector summary
callback payload
```

### 技术关键词

```text
log parser
error signature
embedding
vector search
RAG
LLM summary
evidence-based RCA
```

## 方向三：AI 缺陷归类

### 可行性

可行，而且应该和 AI 日志分析一起做。

建议先定义固定分类，不让 AI 自由发挥：

```text
frontend
backend
jenkins_pipeline
jenkins_agent
scm_gitlab
python_environment
robot_case
testline_configuration
network
environment
product_defect
kpi_generator
kpi_detector
config
unknown
```

### 推荐实现方式

```text
规则分类优先
  -> 如果命中明确 pattern，直接给分类
  -> 如果不明确，再让 LLM 根据 evidence 分类
  -> 输出 confidence
  -> 人工可修正分类
  -> 修正结果进入知识库
```

### 示例

```text
Waiting for next available executor
  -> jenkins_agent

Permission denied publickey
  -> scm_gitlab / credentials

FastAPI 500
  -> backend

React 页面空白 / JS error
  -> frontend

No route to host / timeout
  -> network

Robot variable not found
  -> robot_case / testline_configuration
```

这个方向适合体现：

```text
自动化测试
运维排障
质量 triage
AI 辅助问题定位
```

## 方向四：AI 测试报告

### 可行性

非常可行，且适合做 MVP 展示。

### 报告类型

```text
单次运行报告
  - 本次测试跑了什么
  - 结果如何
  - 失败阶段
  - 失败原因
  - 证据
  - 风险
  - 建议动作

版本回归报告
  - build 维度通过率
  - 失败分布
  - top failure category
  - KPI 异常趋势
  - release risk

晨会 triage 报告
  - 昨天失败了哪些
  - 哪些是环境问题
  - 哪些是疑似产品缺陷
  - 哪些需要 rerun
  - 哪些需要开发介入
```

### 推荐实现

```text
结构化 run 数据 + RCA 结果 + KPI summary
  -> report template
  -> LLM 润色
  -> Markdown / HTML
  -> Portal 展示 / Copy to email
```

注意：

```text
报告最好不要完全让 LLM 从原始日志自由生成。
应先由后端整理结构化事实，再让 LLM 总结和润色。
这样不容易胡说。
```

## 方向五：AI 测试知识库

### 可行性

非常可行，而且是 RAG 的核心。

### 知识库内容

```text
测试规范
  - RF 文档
  - Robot Framework 规范
  - 测试用例设计规范
  - KPI 测试规范

缺陷库
  - 历史 bug
  - root cause
  - workaround
  - owner
  - 修复版本

Jenkins 经验
  - JCasC
  - Job DSL
  - Pipeline
  - agent
  - credentials
  - 常见报错

项目 FAQ
  - testline 怎么配置
  - robotws 怎么 checkout
  - KPI generator 怎么用
  - detector report 怎么看

运行经验
  - 某 testline 常见问题
  - 某 build 常见失败
  - 某类 case flaky 记录
```

### 技术实现

```text
Markdown / JSON / issue / defect records
  -> 文档切片 chunking
  -> embedding
  -> vector store
  -> query
  -> retrieve top-k
  -> LLM answer with citations
```

### 本项目已有素材

```text
docs/
jenkins-integration/kpi_ci_cd_flow.md
issue/
Robot / Jenkins troubleshooting notes
platform-api step 文档
test-workflow-runner step 文档
automation-portal step 文档
```

这些都可以成为 AI 测试知识库素材。

## 方向六：AI Agent 自动调度

### 可行性

可行，但这是最后阶段，而且必须严格分权限。

理想形态：

```text
用户提问：
“帮我分析 T813 最近失败最多的问题，并建议是否 rerun”

AI agent：
1. 查询 platform-api run records
2. 查询 Jenkins build
3. 拉取 artifact
4. 查询知识库
5. 生成 RCA
6. 给出建议
7. 请求用户确认是否 rerun
8. 用户确认后才调用 Jenkins trigger
```

### 不建议一开始开放的能力

```text
AI 自动 push 代码
AI 自动改 DB
AI 自动重启 Jenkins
AI 自动 rerun 大量 job
AI 自动改配置
```

### 权限分级

```text
Level 1：只读 agent
  - 查 Jenkins
  - 查 DB
  - 查 artifact
  - 查知识库
  - 总结问题

Level 2：受控执行 agent
  - 用户确认后 trigger Jenkins
  - 用户确认后 rerun failed case
  - 用户确认后生成 Jira draft

Level 3：高权限 agent
  - 改配置
  - 改代码
  - 改数据库
  - 重启服务
```

当前项目现阶段最多做到：

```text
Level 1 + 部分 Level 2
```

## 推荐技术架构

```text
automation-portal
  -> AI Insight / AI Copilot UI

platform-api
  -> ai_analysis_service
  -> ai_report_service
  -> ai_knowledge_service
  -> ai_agent_orchestrator

evidence layer
  -> Jenkins console
  -> artifacts
  -> Robot reports
  -> KPI outputs
  -> DB run records

RAG layer
  -> document loader
  -> chunking
  -> embeddings
  -> vector store
  -> retrieval

LLM layer
  -> prompt templates
  -> summary
  -> RCA
  -> report generation
  -> test case draft generation

tool layer
  -> Jenkins API
  -> GitLab/GitHub API
  -> DB query
  -> platform-api internal API
  -> artifact fetcher
```

## 推荐落地顺序

不要六个方向一起做。

建议按下面顺序：

### Phase 1：AI 日志分析 + AI 缺陷归类 + AI 报告

这是最容易落地的 MVP。

目标：

```text
让平台能读懂 Jenkins / Robot / runner 的失败证据，
自动输出失败摘要、缺陷归类、RCA 建议和测试报告。
```

### Phase 2：AI 测试知识库 RAG

目标：

```text
把 Jenkins 经验、RF 文档、缺陷案例、FAQ 接进去。
```

### Phase 3：AI 自动生成测试用例 / workflow_spec 草案

目标：

```text
先生成草案，人确认后执行。
```

### Phase 4：AI Agent 只读分析

目标：

```text
能查 Jenkins、DB、artifact、知识库，但不自动执行。
```

### Phase 5：AI Agent 受控调度

目标：

```text
用户确认后触发 Jenkins、rerun、生成 Jira draft。
```

## 最关键判断

这个想法可行，而且比单纯“做一个 AI chat”更像真实企业项目。

原因是这个项目有真实数据闭环：

```text
需求 / 代码 / Jenkins / Robot / KPI / 缺陷 / 文档 / 报告
```

AI 正好可以在这些地方发挥作用：

```text
生成测试设计
理解失败日志
检索历史经验
归类缺陷
总结报告
辅助调度
```

当前阶段最重要的一句话：

```text
AI 先做分析助手，再做执行助手，最后才做调度 agent。
```

对当前项目，最合理的第一版是：

```text
AI Evidence + AI RCA + AI Report + RAG Knowledge Base
```

这个方向最稳，也最容易展示成：

```text
AI-Driven Intelligent Testing Platform
```

## 后续讨论问题

下一轮收口最终方案前，建议继续讨论：

```text
1. 第一版是否先只做 rules-first AI analysis，不接外部 LLM？
2. RAG 知识库第一批文档范围选哪些？
3. embedding 和 vector store 用本地方案还是云服务？
4. AI agent 第一阶段是否只允许 read-only？
5. Portal 里先做 Run Detail AI Insight，还是先做全局 AI Copilot？
```
