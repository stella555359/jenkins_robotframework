# UTE TAF MCP Server User Guide

## 文档定位

这份文档根据本地保存的 4 份内部 HTML 文档整理：

- `Test Auto Doc MCP`
- `Installation Guide`
- `MCP Tools Reference`
- `Agent Setup`

目标是把 `test-auto-doc-mcp` 的使用方式整理成适合 `C:\TA\jenkins_robotframework` 项目长期回看的 user guide。

一句话结论：

```text
UTE TAF MCP Server 是给 Cursor / Claude Desktop 等 AI 客户端使用的本地 MCP server。
它通过 tools 访问 UTE TAF Knowledge Base、TAF library 文档、UEVT 文档、automation strategy 和 troubleshooting 信息，
用于让 AI 在生成测试代码、解释 TAF API、设计 Robot / Python 自动化用例时先查内部权威文档，减少幻觉。
```

## 1. 它解决什么问题

普通 AI 模型不一定知道 Nokia 内部 TAF / UTE / SBTS / vCU / COAM / UEVT 等知识，也不一定知道内部 Python library、Robot Framework keyword、UE 管理方式、TAF library 参数和返回值。

`test-auto-doc-mcp` 的作用是把这些内部知识以 MCP tools 的形式暴露给 Cursor：

```text
用户问题 / 代码任务
  -> Cursor agent 判断这是 TAF / UTE / Nokia domain 问题
  -> 调用 test-auto-doc MCP tools
  -> 从 UTE TAF Knowledge Base / vector search / structured API 取回资料
  -> 再基于检索结果回答、生成代码或给排障建议
```

它当前支持 MCP `Tools` 能力，不支持 `Prompts`、`Resources`、`Roots`、`Elicitation`、`Sampling`。

## 2. 安装前提

官方文档要求：

- Python `3.10` 或更新版本。
- 能访问 Knowledge Base API endpoint，默认是 `https://ute-knowledge-provider.ext.net.nokia.com`。
- 能从公司 Artifactory 安装 Python package。

如果本地 pip / pipx 还没有配置公司 Artifactory，需要先按下面的 TAF package source 步骤配置。

### 2.1 配置 TAF package source

内部 TAF package installation guide 的核心要求是：

```text
TAF Python packages 存放在 Artifactory。
匿名访问 Artifactory 已经移除。
下载安装 package 时必须使用用户名和 identity token。
```

生成 pip 配置的步骤：

1. 登录 Artifactory：

```text
https://artifactory-espoo2.int.net.nokia.com/ui/login
```

2. 打开右上角 `User Profile`。
3. 点击 `Set Me Up`。
4. 选择 package type 为 `pypi`。
5. 在 `Set Up A Pypi Client` 弹窗中选择：

```text
Repository: ute-pypi-virtual
Client: Pip
```

6. 在 `Your JFrog account Password` 输入框里输入当前 Artifactory 账号的密码。

这里不需要再输入 account / username，因为你已经登录 Artifactory，系统会用当前登录用户生成 identity token。

7. 点击 `Generate Token & Create Instructions`。
8. 页面提示 `The token has been generated successfully!` 后，会显示两段内容：

```text
第一段：生成出的 identity token。
第二段：可复制到 ~/.pip/pip.conf 的 pip 配置。
```

9. 复制第二段 `pip.conf` 配置到本机 pip 配置中。配置里的 URL 会自动包含当前用户名和生成的 token。

TAF guide 中给出的默认 package index URL 格式：

```text
https://<username>:<token>@artifactory-espoo2.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple
```

不同系统下 pip 用户级配置文件路径不同。

Linux / WSL / Git Bash 下通常写入：

```text
$HOME/.pip/pip.conf
```

如果目录不存在，可以先创建：

```bash
mkdir -p ~/.pip
```

Windows PowerShell 下不要使用 `C:\Users\<user>\.pip\pip.conf`。Windows pip 用户级配置通常是：

```text
%APPDATA%\pip\pip.ini
```

例如当前用户可能是：

```text
C:\Users\stlin\AppData\Roaming\pip\pip.ini
```

最稳妥的方式是让 pip 自己写入正确位置：

```powershell
pip config set global.index-url "https://<username>:<token>@artifactory-espoo2.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple"
pip config list
pip config debug
```

`pip config list` 应能看到 `global.index-url`；`pip config debug` 可以查看当前 pip 实际读取了哪些配置文件。

配置文件示例内容：

```ini
[global]
index-url = https://<username>:<token>@artifactory-espoo2.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple
```

也可以在单次安装时通过 `-i` 指定 index URL：

```bash
pip install PACKAGE_NAME -i https://<username>:<token>@artifactory-espoo2.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple
```

注意：

- `<token>` 应使用 Artifactory identity token，不要使用普通密码。
- 生成出来的 token 只在本机配置使用，不要写入项目文档。
- 不要把包含真实 token 的 `pip.conf`、`pip.ini`、命令历史或截图提交到 Git。
- 如果 token 已经出现在截图、聊天记录或共享文档中，建议在 Artifactory 中撤销旧 token 并重新生成。
- 如果公司不同站点有更近的 Artifactory virtual instance，可以按实际地点替换 index URL。

TAF guide 提到的其他站点 URL：

```text
Bangalore:
https://artifactory-blr1.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple

Hangzhou:
https://artifactory-hz1.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple

Franklin Park:
https://artifactory-fpark1.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple
```

## 3. 推荐安装方式

本地 Cursor 使用推荐通过 `pipx` 安装，因为 `pipx` 会把命令安装到全局 `PATH`，同时保持隔离环境。这样 Cursor 才能自动启动 MCP server 进程。

```bash
pipx install test-auto-doc-mcp
```

如果不想写全局 pip 配置，也可以只给这一次 `pipx install` 传 Artifactory index：

```bash
pipx install test-auto-doc-mcp --pip-args "-i https://<username>:<token>@artifactory-espoo2.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple"
```

如果还没有 `pipx`：

```bash
pip install pipx
pipx ensurepath
```

服务器、容器、CI 或开发环境里如果自己管理 virtualenv，可以使用：

```bash
pip install test-auto-doc-mcp
```

或显式指定 TAF Artifactory：

```bash
pip install test-auto-doc-mcp -i https://<username>:<token>@artifactory-espoo2.int.net.nokia.com/artifactory/api/pypi/ute-pypi-virtual/simple
```

从源码开发时使用：

```bash
pip install -e .
```

## 4. 安装验证

安装后先确认命令存在：

```bash
test-auto-doc --help
```

最小本地启动方式：

```bash
test-auto-doc
```

默认 transport 是 `stdio`，这是本地 Cursor 接入最常用的方式。正常情况下，不需要你手工长期运行这个命令；配置好 Cursor 后，Cursor 会自动启动它。

## 5. Cursor MCP 配置

把 server 加到 Cursor 的 MCP 配置文件中：

```json
{
  "mcpServers": {
    "test-auto-doc": {
      "command": "test-auto-doc"
    }
  }
}
```

官方文档使用的配置文件路径是：

```text
~/.cursor/mcp.json
```

在 Windows 上可以理解为用户目录下的 Cursor MCP 配置，例如：

```text
C:\Users\<your-user>\.cursor\mcp.json
```

配置含义：

```text
Cursor 启动 / 需要调用 MCP 时，执行 test-auto-doc 命令。
Cursor 通过 stdio 和这个本地 server 通信。
server 再访问 UTE TAF Knowledge Base。
```

## 6. MCP Tools 清单

### 6.1 文档语义搜索类

`query_taf_documentation`

- 用途：对 TAF documentation 做 semantic search。
- 适合问题：TAF functionality、base station automation、SBTS、VRAN、UE automation、measurement equipment automation、API / device access。
- 输入：`query` 必填，`n_results` 可选。

`query_automation_strategy`

- 用途：查询 Nokia test automation strategy。
- 适合问题：产品级自动化策略、SBTS / VRAN / UE automation / measurement equipment 的测试自动化方式、API 和 library 使用建议。
- 输入：`query` 必填，`n_results` 可选。

`query_agents_documentation`

- 用途：查询 UTE agents 文档。
- 适合问题：agent 配置、部署、使用方式、不同 test agents 如何工作。
- 输入：`query` 必填，`n_results` 可选。

`query_uevt_documentation`

- 用途：查询 UE / UEVT 相关文档。
- 适合问题：TAF UE supported devices、Attach / Detach UE、Nokia Android Application、UE proxy、UE 安装指南等。
- 输入：`query` 必填，`n_results` 可选。

### 6.2 TAF library 结构化查询类

`list_taf_libraries`

- 用途：列出 Knowledge Base 中注册的所有 TAF libraries。
- 适合场景：不知道 library 准确名称时先发现可用库。
- 输入：无参数。
- 输出：library summary，通常包括 status、version、function/example 数量。

`get_taf_library`

- 用途：获取指定 TAF library 的详细信息。
- 适合场景：确认 library URL、状态、版本、functions 和 examples。
- 输入：`library_name`。

`list_taf_library_functions`

- 用途：列出指定 library 里的所有 functions。
- 适合场景：想知道某个 library 提供哪些能力。
- 输入：`library_name`。

`get_taf_library_function`

- 用途：获取某个 library 里指定 function 的完整文档。
- 适合场景：需要准确参数、返回值、限制条件、调用方式。
- 输入：`library_name`、`function_name`。

`get_taf_library_examples`

- 用途：获取某个 library 的所有代码示例。
- 适合场景：让 AI 基于真实 Python / Robot Framework 示例生成测试代码。
- 输入：`library_name`。

`get_taf_library_function_examples`

- 用途：获取某个 function 的使用示例。
- 适合场景：需要具体 function 的实战用法。
- 输入：`library_name`、`function_name`。

`get_taf_troubleshooting`

- 用途：获取指定 TAF library 的 troubleshooting handbook。
- 适合场景：library 调用失败、环境问题、已知问题、workaround 查询。
- 输入：`library_name`。

所有 tools 的 output schema 在官方文档里都是 string，也就是说 Cursor 最终拿到的是一段可读文本，再交给 agent 做解释、总结或代码生成。

## 7. 官方推荐的 Agent Setup

只安装 MCP server 还不够。官方文档特别强调：MCP-capable agent 不会天然知道什么时候该调用这个 server，也不知道应该查询哪个 vectorstore，更不理解 Nokia 内部缩写。

所以官方建议把配套的 `.cursor/rules` 和 `.cursor/skills` 从 `test-auto-doc-mcp-setup` 仓库复制到自己的 `.cursor/` 目录。

内部 GitLab 仓库入口：

```text
https://wrgitlab.ext.net.nokia.com/TAF/ai/test-auto-doc-mcp-setup/-/tree/main/configs/.cursor?ref_type=heads
```

仓库和目录可以理解为：

```text
TAF/ai/test-auto-doc-mcp-setup
  configs/.cursor/
    rules/
    skills/
```

核心原因：

```text
没有 rules / skills：
  Agent 可能直接凭训练数据回答，导致过时、局部或编造内容。

有 rules / skills：
  Agent 更容易识别 TAF / UTE / Nokia domain 问题，
  并主动调用 MCP tools 查权威资料后再回答。
```

### 7.1 推荐规则和技能

`01-nokia-domain-knowledge.mdc`

- 类型：always-on vocabulary。
- 用途：告诉 agent 哪些词属于 Nokia domain，例如 TAF、UTE、SBTS、vCU、vDU、gNB/eNB、COAM、SCF、NETCONF、OAM、RFRL、WTS、UE、UEVT、NetAct。
- 还包含 TAF library 命名习惯，例如 `taf.*`、`ta_*`、`ta5g_*`、`rfsw.*`。
- 效果：当这些词出现时，agent 应把问题视为 Nokia 内部领域问题，并优先查 Knowledge Base。

`02-knowledge-base-exploration.mdc`

- 类型：search methodology。
- 用途：要求 agent 在回答事实性问题前按 `Decomposition -> Deepening -> Exploration -> Coverage check` 的方式检索。
- 效果：不是只搜一个关键词，而是扩展同义词、缩写、相关概念，并覆盖定义、限制、步骤和边界情况。

`ute-taf-mcp-agentic-flow`

- 类型：task-triggered skill。
- 用途：当任务涉及 TAF 代码修改、TAF library 故障排查、API/usage 问题时，触发一套具体 MCP 查询流程。
- 故障策略：MCP 不可用时重试一次，然后提示用户答案可能不完整，再 fallback。

### 7.2 安装位置

项目级安装：

```text
<repo-root>/.cursor/
  rules/
    01-nokia-domain-knowledge.mdc
    02-knowledge-base-exploration.mdc
  skills/
    ute-taf-mcp-agentic-flow/
      SKILL.md
```

适合把规则随项目提交，让所有协作者共享同一套 agent 行为。

用户全局安装：

```text
~/.cursor/
  rules/
    01-nokia-domain-knowledge.mdc
    02-knowledge-base-exploration.mdc
  skills/
    ute-taf-mcp-agentic-flow/
      SKILL.md
```

适合多个 TAF 相关仓库共用。

官方说明：项目级和用户全局可以共存，项目级优先，全局作为 fallback。Cursor 会在下一轮自动发现这些 rules / skills。

## 8. 在 jenkins_robotframework 项目中的用法

本项目当前定位是 5G gNB / KPI 自动化测试平台，涉及 Jenkins、Robot Framework、TAF/UTE 执行环境、testline、robotws、testline_configuration、KPI 后处理和 AI 化演进。

`test-auto-doc-mcp` 在本项目里最适合放在“开发和测试设计阶段”，不是直接放在 Jenkins runtime 里。

推荐使用场景：

- 生成或改写 Robot Framework case 前，先查询相关 TAF / UTE library 和示例。
- 分析 `robotws`、`testline_configuration`、UEVT 或 test agent 相关问题时，先查内部文档。
- 给 Jenkins pipeline 增加真实 Robot 执行参数前，查询 TAF/UTE agent、UE 或 library 使用方式。
- 设计 AI 测试用例生成流程时，把 MCP 查询结果作为 grounding evidence，避免 AI 编造不存在的 keyword 或 API。
- 排查 TAF library 报错时，调用 `get_taf_troubleshooting` 找已知问题和 workaround。

不建议第一阶段这样用：

- 不建议直接把这个本地 Cursor MCP server 当成 Jenkins 生产流水线依赖。
- 不建议把它和 Insights Fusion runtime MCP 混为一谈。
- 不建议让 AI 在没有 MCP 查询证据的情况下直接生成 TAF library 调用代码。

更稳妥的项目流程：

```text
需求 / 问题
  -> Cursor 中描述 TAF / UTE / Robot / KPI 自动化目标
  -> Cursor rules 识别 Nokia domain
  -> skill 触发 test-auto-doc MCP 查询
  -> AI 基于查询结果生成测试设计 / Robot case / Python helper 草稿
  -> 人工复核 API、参数、环境变量和执行路径
  -> 再进入 Jenkins / Robot / KPI runner 实际验证
```

## 9. 典型 Prompt 示例

查询 TAF library：

```text
请先通过 test-auto-doc MCP 查询和 UE attach/detach 相关的 TAF / UEVT 文档，
总结可用 library、关键函数、参数和示例，再帮我设计一个 Robot Framework 自动化用例草稿。
```

查询 automation strategy：

```text
请使用 test-auto-doc MCP 查询 Nokia test automation strategy，
说明 gNB E2E KPI 回归场景中，哪些部分适合用 Robot Framework，
哪些部分适合用 Python runner 做后处理。
```

查询 troubleshooting：

```text
这个 TAF library 调用失败，请先用 get_taf_troubleshooting 查询该 library 的已知问题和 workaround，
再结合下面的 Jenkins console log 给出排障步骤。
```

查询 UTE agent：

```text
请用 query_agents_documentation 查询 UTE test agent 的部署和使用方式，
重点关注 Jenkins 通过 agent 执行 Robot case 时需要准备哪些环境信息。
```

## 10. 验证命令与预期结果

本步骤不主动在本机或服务器执行验证命令。请用户按需在本地 Windows / 公司网络环境下验证。

### 10.1 安装验证

命令：

```bash
test-auto-doc --help
```

预期结果：

```text
能看到 test-auto-doc 命令帮助信息，说明 CLI entrypoint 已安装到 PATH。
```

常见失败：

- `command not found` / `not recognized`：`pipx` 安装路径没有进入 `PATH`，需要执行 `pipx ensurepath` 后重开终端。
- package 找不到：pip / pipx 没有配置公司 Artifactory，或没有使用 `ute-pypi-virtual` index URL。
- `401` / `403`：Artifactory 用户名或 identity token 不正确，或 token 已过期。
- 网络访问失败：当前电脑未连接公司网络 / VPN，或无法访问 Knowledge Base API endpoint。

### 10.2 最小启动验证

命令：

```bash
test-auto-doc
```

预期结果：

```text
server 以 stdio transport 启动，不应立即报 Python import error、package missing 或 endpoint 配置错误。
```

常见失败：

- Python 版本低于 `3.10`。
- 缺少依赖包。
- 内部 Knowledge Base endpoint 不可达。

### 10.3 Cursor 验证

操作：

```text
1. 配置 ~/.cursor/mcp.json。
2. 重启 Cursor 或重新加载窗口。
3. 在 Cursor MCP / Tools 相关页面确认 test-auto-doc server 可用。
4. 在聊天中提出 TAF / UTE 相关问题，观察 agent 是否调用 test-auto-doc tools。
```

预期结果：

```text
Cursor 能发现 test-auto-doc MCP server，并能在需要时调用 tools 返回文档检索结果。
```

常见失败：

- `test-auto-doc` 不在 Cursor 进程的 PATH 中。
- `mcp.json` JSON 格式错误。
- 公司网络不可达。
- 未安装 rules / skills，导致 agent 虽然有 tools，但不主动调用。

## 11. 本轮学习记录

本轮解决的问题：

```text
把内部 UTE TAF MCP Server 的 4 份 HTML 文档整理为项目内可恢复、可复用的 user guide，
并补充 TAF package installation guide 中关于 Artifactory / pip / pipx package source 的配置步骤。
根据实际 Artifactory Set Up A Pypi Client 页面，补充 Repository、Client、password、identity token 生成和 pip.conf 复制步骤。
```

改动文件：

```text
新增并持续更新 docs/ai/ute-taf-mcp-server-user-guide.md
```

核心调用流：

```text
Cursor user prompt
  -> Cursor rules / skills 判断是否为 TAF / UTE / Nokia domain
  -> test-auto-doc MCP tool call
  -> UTE TAF Knowledge Base / vector search / structured API
  -> tool 返回 string
  -> Cursor agent 基于权威文档生成回答 / 测试设计 / 代码草稿
```

关键字段和工具：

- `mcpServers.test-auto-doc.command`：Cursor 用来启动 MCP server 的命令，值为 `test-auto-doc`。
- `query`：语义搜索类 tools 的核心输入。
- `n_results`：语义搜索返回条数，可选。
- `library_name`：TAF library 结构化查询的核心输入。
- `function_name`：查询具体 function 文档或示例时使用。
- `index-url`：pip / pipx 下载 TAF package 时使用的 Artifactory PyPI index。
- `identity token`：Artifactory 鉴权 token，用于替代匿名访问或普通密码。

给用户的复盘问题：

1. 我是否能讲清楚 `test-auto-doc-mcp` 是开发阶段辅助工具，而不是 Jenkins runtime 的核心依赖？
2. 我是否能讲清楚 MCP tools、Cursor rules、Cursor skills 三者的分工？
3. 我是否能说明为什么内部 TAF / UTE 问题需要先查 Knowledge Base，不能让 LLM 直接猜？
4. 我是否能基于一个 Robot case 需求，设计出“先查 MCP，再生成草稿，再人工复核，再 Jenkins 验证”的流程？
5. 我是否能独立说明为什么安装 TAF package 前需要配置 Artifactory，并知道 `401` / `403` 常见是 token 或权限问题？

## 12. MCP 实操练习记录：SBTS Cell Lock / Unlock Testcase

练习问题：

```text
Create a testcase for SBTS where base station cells are locked and unlocked in loop
```

本次 MCP 查询路径：

```text
query_taf_documentation(
  "SBTS base station cell lock unlock loop Robot Framework TAF API lock cell unlock cell COAM admin state"
)

query_taf_documentation(
  "taf.sbts.oam.coam.admin lock unlock generic function dist_name NRCELL_R Robot Framework example connect to bts_host bts_port connection"
)

query_taf_documentation(
  "TAF SBTS collect snapshot failed attempt Robot Framework keyword collect snapshot base station snapshot failure logs"
)
```

MCP 查到的核心信息：

- SBTS cell admin 相关库是 `taf.sbts.oam.coam.admin`。
- 旧接口 `lock_cell` / `unlock_cell` 存在，但文档标注为 deprecated。
- 推荐使用通用接口 `lock` / `unlock`。
- `lock` / `unlock` 支持 `dist_name`，可用于 `<BBMOD|RMOD|ASIRMOD|TTRX_ST|LANE|NRDU|NRCELL|NRCELLGRP|LNCEL distName>`。
- `connection` 可传 `AdminConnection` 或连接别名。
- `timeout` 用于等待操作完成。
- snapshot 相关候选包括 `taf.collectors.snapshot`、`taf.selenium.sbts collect_snapshot`、`taf.selenium.sbts_fsm3 collect_snapshot`，但具体应该使用哪一个取决于实验室环境和 SBTS 访问方式。

本次生成的练习文件：

```text
C:\TA\taf_mcp_practise\taf_mcp_practise.robot
```

练习文件做了什么：

- 引入 `taf.sbts.oam.coam.admin WITH NAME coam`。
- 通过 `coam.connect_to` 连接 SBTS cOAM。
- 使用 `coam.lock` / `coam.unlock` 对 `NRCELL` distName 做循环 lock/unlock。
- 每次操作失败时进入 `Collect Failure Snapshot` 占位 keyword。
- `Collect Failure Snapshot` 当前不绑定具体 collector，避免在没有目标 testline 信息时编造 snapshot API。
- `FINALLY` 中调用 `coam.teardown` 关闭连接。

验证命令：

```bash
robot --dryrun C:\TA\taf_mcp_practise\taf_mcp_practise.robot
```

预期结果：

```text
Robot Framework 能完成 dry-run 语法检查。
由于本文件依赖内部 TAF library 和 testline 变量，真实执行需要在具备 TAF/UTE 环境的目标机器上进行。
```

常见失败判断：

- `Library 'taf.sbts.oam.coam.admin' not found`：本地没有安装对应 TAF package，或没有在正确 venv / testline 环境运行。
- `${tl.gnbs...}` 变量不存在：当前执行环境没有加载 testline configuration。
- `coam.connect_to` keyword 找不到：库版本或 keyword 命名需要按目标环境确认，必要时用 MCP 查询该 library functions。
- lock/unlock 真实执行失败：检查 `dist_name` 是否匹配目标 SBTS，检查 cOAM 连接、端口和权限。
- snapshot hook 未采集真实 snapshot：需要按目标实验室选择 `taf.collectors.snapshot` 或 `taf.selenium.sbts` 相关 collector 后再替换占位 keyword。

## 13. MCP 实操练习记录：UE Attach / Detach Testcase

练习问题：

```text
Create a testcase for UE attach detach for specific sbts cell, need support different ue types
```

本次 MCP 查询路径：

```text
query_uevt_documentation(
  "UE attach detach Robot Framework TAF supported UE types taf.ue.android taf.ue.at UE proxy attach detach specific cell SBTS"
)

query_taf_documentation(
  "TAF UE attach detach Robot Framework keyword attach UE detach UE taf.ue.android taf.ue.at specific cell SBTS"
)

query_uevt_documentation(
  "Require Ue Robot Framework capabilities ANDROID_UE IPHONE AT FASTMILE taf.ue proxy available robot keywords different UE types"
)

query_taf_documentation(
  "taf.ue.android require_ue starting_cell starting_enb cell alias attach to specific cell Robot Framework"
)
```

MCP 查到的核心信息：

- `taf.ue` 是 Robot Framework 使用的统一入口。
- 常用关键词包括 `Require Ue`、`Attach Ue`、`Detach Ue`、`Log Ue Info`。
- `Attach Ue` 的目标是让 UE attach 到 cell，并允许 UE 使用目标技术的连接能力。
- `Detach Ue` 会让 UE 从 cell detach，移动天线相关物理通信会被关闭，但 Wi-Fi / Bluetooth 可能仍保持开启。
- `Attach Ue` / `Detach Ue` 支持 Android、iPhone、AT、Fastmile 等不同 UE 类型。
- `taf.ue.proxy` 用于统一 Robot Framework 与 UE PC 之间的通信模型。
- `taf.ue.proxy` 的 multi-device 能力可以在单个 proxy server 中加载多个 access layers，例如 `android`、`at`、`iphone`、`fastmile`、`mtk`。
- Android 的 `Require Ue` 支持 `starting_cell`。
- iPhone / AT 文档中 `starting_cell` 标注为 `NOT SUPPORTED`。
- UE 失败排查时建议收集 `robot.html`、配置文件、`ute_ue logs`、`taf.ue.proxy logs`、`moler logs`、`proxy_mngr.log`、Android `logcat` 等。

本次生成的练习文件：

```text
C:\TA\taf_mcp_practise\ue_attach_detach.robot
```

练习文件做了什么：

- 引入 `taf.ue` 和 `Collections`。
- 用 `@{UE_TYPES_TO_TEST}` 管理要覆盖的 UE 类型：`android`、`iphone`、`at`、`fastmile`。
- 用 `&{UE_ALIAS_BY_TYPE}` 和 `&{UE_CAPABILITY_BY_TYPE}` 管理 UE alias 和 capability。
- Android 场景使用 `Require Ue ... starting_cell=${TARGET_SBTS_CELL}`。
- 非 Android 场景只按 capability reserve UE，并在日志中提示 `starting_cell` 不适用或需要目标环境确认。
- 对每种 UE 类型执行 `Attach Ue`、`Log Ue Info`、`Detach Ue`。
- 失败时进入 `Collect UE Failure Evidence` 占位 keyword，记录应该收集的 UE 相关证据。

验证命令：

```bash
robot --dryrun C:\TA\taf_mcp_practise\ue_attach_detach.robot
```

预期结果：

```text
Robot Framework 能完成 dry-run 语法检查。
真实执行需要目标机器具备 taf.ue、UE proxy、UE access layer、testline configuration 和实际 UE 设备。
```

常见失败判断：

- `Library 'taf.ue' not found`：当前环境没有安装 `taf.ue` 或没有进入正确 TAF venv。
- `Require Ue` 找不到匹配 UE：`capabilities` 和 testline 中的 UE 配置不匹配。
- Android 使用 `starting_cell` 失败：检查 `${TARGET_SBTS_CELL}` 是 E-UTRAN cell identifier 还是 cell alias，并确认 testline 配置支持。
- iPhone / AT 不能按 specific cell reserve：MCP 文档标注 `starting_cell` 不支持，需要改用目标环境支持的 UE 选择方式。
- `Attach Ue` / `Detach Ue` 失败：检查 UE proxy、ADB / iPhone / AT driver、Nokia Android Application、SIM、cell 状态和信号覆盖。
- 日志不完整：按 UEVT 文档补齐 `ute_ue logs`、`taf.ue.proxy logs`、`moler logs`、`proxy_mngr.log` 或 `logcat`。

### 13.1 Python 生成 Robot testcase 版本

用户进一步要求：

```text
please use python code to generate the testcase for UE attach detach for specific sbts cell and multi type ues
```

新增 Python generator：

```text
C:\TA\taf_mcp_practise\generate_ue_attach_detach_testcase.py
```

这个脚本把 UE 类型、UE alias、capability、是否支持 `starting_cell` 这些信息放在 Python 配置中：

```text
android:
  alias = ANDROID_UE
  capability = ANDROID_UE_1
  supports_starting_cell = True

iphone:
  alias = IPHONE_UE
  capability = IPHONE_UE_1
  supports_starting_cell = False

at:
  alias = AT_UE
  capability = AT_UE_1
  supports_starting_cell = False

fastmile:
  alias = FASTMILE_UE
  capability = FASTMILE_UE_1
  supports_starting_cell = False
```

生成命令：

```powershell
cd C:\TA\taf_mcp_practise
python .\generate_ue_attach_detach_testcase.py --output .\ue_attach_detach.robot
```

如果要指定目标 cell：

```powershell
python .\generate_ue_attach_detach_testcase.py `
  --target-cell "CELL_ALIAS_OR_EUTRAN_CELL_ID" `
  --output .\ue_attach_detach.robot
```

如果要调整 Android attach/detach timeout：

```powershell
python .\generate_ue_attach_detach_testcase.py `
  --target-cell "CELL_ALIAS_OR_EUTRAN_CELL_ID" `
  --attach-timeout 90 `
  --output .\ue_attach_detach.robot
```

设计意义：

- Robot testcase 的结构由 Python 统一生成，避免手工复制多 UE 分支。
- 后续如果新增 UE 类型，只需要在 `UE_TYPES` 中追加配置。
- `starting_cell` 支持差异在 Python 配置中显式表达，避免对 iPhone / AT 生成不支持的参数。
- Python generator 可以后续扩展为从 YAML / JSON / testline 配置读取 UE 类型和 capability。

验证命令：

```powershell
python .\generate_ue_attach_detach_testcase.py --help
python .\generate_ue_attach_detach_testcase.py --output .\ue_attach_detach.robot
robot --dryrun .\ue_attach_detach.robot
```

预期结果：

```text
Python 脚本能生成 ue_attach_detach.robot。
Robot dry-run 能完成语法检查。
真实执行仍依赖目标 TAF/UTE 环境、taf.ue、UE proxy、testline configuration 和实际 UE 设备。
```

### 13.2 Direct Python 实现版本

用户进一步澄清：

```text
我的意思是可以直接用 python 来实现 UE attach detach 吗，不必采用 Robot Framework case 的方式。
```

结论：

```text
可以。
MCP 文档里 `taf.ue.android`、`taf.ue.iphone`、`taf.ue.at` 等库都暴露了 Python function 文档，
包括 require_ue、attach_ue、detach_ue。
```

本次新增 direct Python 练习文件：

```text
C:\TA\taf_mcp_practise\ue_attach_detach_direct_python.py
```

MCP 查询到的 direct Python API 信息：

- `taf.ue.android.require_ue`
  - `ue_alias`
  - `capabilities`
  - `starting_cell`
  - `starting_enb`
  - `starting_phy_cell`
- `taf.ue.android.attach_ue`
  - `ue_alias`
  - `timeout`
  - `validation`
  - `top_cmd_only`
  - 可能抛出 `UeProcedureError`、`UeProcedureTimeout` 等异常。
- `taf.ue.android.detach_ue`
  - `ue_alias`
  - `timeout`
  - `validation`
  - `top_cmd_only`
  - 可选 `force_change_mode`。
- `taf.ue.iphone.attach_ue` / `detach_ue`
  - 支持 `ue_alias`、`validation`。
  - `timeout` / `top_cmd_only` 文档中标注为不支持。
- `taf.ue.at.attach_ue` / `detach_ue`
  - 支持 `ue_alias`、`validation`。
  - `starting_cell` 文档中标注为不支持。

Direct Python 脚本设计：

- 用 `UeTypeConfig` 描述 UE 类型、alias、capability、是否支持 `starting_cell`。
- 用 `load_ue_api()` 按 UE 类型加载 Python API。
- Android 使用 `require_ue(..., starting_cell=target_cell)`。
- iPhone / AT 使用 capability reserve，不传 `starting_cell`。
- Android attach/detach 传 `timeout`、`validation`、`top_cmd_only`。
- 非 Android attach/detach 只传通用参数，避免生成文档标注不支持的参数。
- `collect_failure_evidence()` 作为证据收集占位函数，后续可接入 UE logs、proxy logs、logcat 等。

运行示例：

```powershell
cd C:\TA\taf_mcp_practise
python .\ue_attach_detach_direct_python.py --target-cell "CELL_ALIAS_OR_EUTRAN_CELL_ID" --ue-types android
```

多 UE 类型：

```powershell
python .\ue_attach_detach_direct_python.py `
  --target-cell "CELL_ALIAS_OR_EUTRAN_CELL_ID" `
  --ue-types android,iphone,at `
  --timeout 60
```

只做 top-level Android attach/detach 操作：

```powershell
python .\ue_attach_detach_direct_python.py `
  --target-cell "CELL_ALIAS_OR_EUTRAN_CELL_ID" `
  --ue-types android `
  --top-cmd-only
```

验证重点：

```text
第一步不是直接真实执行，而是先在目标 TAF virtualenv 中确认 import path 是否正确。
```

原因：

```text
MCP 文档确认了 function 名称和参数，
但不同 TAF package 版本的 Python import path 可能不同。
```

常见失败判断：

- `ModuleNotFoundError: taf.ue.android`：当前 venv 没安装对应 TAF package，或 import path 与安装版本不一致。
- `UnknownAlias`：没有先成功 `require_ue`，或 alias 不匹配。
- `RequiredUeNotFound`：capability / starting_cell 与 testline 中的 UE 配置不匹配。
- `UeProcedureTimeout`：attach/detach 超时，检查 UE proxy、信号、cell、SIM、NAA/ADB/driver。
- `UeProcedureError`：UE 操作失败，需要收集 `ute_ue logs`、`taf.ue.proxy logs`、`logcat` 等证据。

后续改进方向：

- 让脚本从 YAML / JSON 读取 UE type、alias、capability、target cell。
- 将 `collect_failure_evidence()` 接入真实日志收集。
- 将 direct Python flow 封装进 Jenkins runner，而不是只作为本地练习脚本。

## 14. MCP 实操练习记录：Python PA Handover + gNB Wireshark

练习问题：

```text
请用 python 实现通过调节 source cell 和 target cell 的 PA 实现 SBTS cell handover 的功能，
从 source cell 切到 target cell，适配不同 PA 类型，handover 期间抓取 gNB Wireshark。
```

本次 MCP 查询路径：

```text
query_taf_documentation(
  "SBTS handover source cell target cell PA power attenuator programmable attenuator TAF Python library adjust PA cell handover"
)

query_taf_documentation(
  "TAF programmable attenuator PA type set attenuation source cell target cell handover Python API"
)

query_taf_documentation(
  "TAF gNB wireshark packet capture tcpdump pcap collector start stop capture gnb interface Python API"
)

get_taf_library_function("taf.hw.rf_attenuator", "setup_attenuator")
get_taf_library_function("taf.hw.rf_attenuator", "set_linear_fading_scenario")
get_taf_library_function("taf.hw.rf_attenuator", "set_ports_fading_attenuation")
get_taf_library_examples("taf.hw.rf_attenuator")

get_taf_library_function("taf.gnb.oam.coam.cu", "connect_to")
get_taf_library_function("taf.gnb.oam.coam.cu", "start_ip_traffic_capture")
get_taf_library_function("taf.gnb.oam.coam.cu", "stop_ip_traffic_capture")
get_taf_library_function("taf.collectors.ip_traffic_capturing", "create_vcu_ip_traffic_capturing_file_collector")
get_taf_library_examples("taf.collectors.ip_traffic_capturing")
```

MCP 查到的核心信息：

- PA / attenuator 控制：
  - `taf.hw.rf_attenuator.setup_attenuator`
  - `taf.hw.rf_attenuator.set_linear_fading_scenario`
  - `taf.hw.rf_attenuator.set_ports_fading_attenuation`
  - JFW attenuator 支持 linear fading scenario。
  - `taf.hw.azimuth.channel_emulator.api.DirectedLink.set_link_atten` 可设置 Azimuth channel emulator link attenuation。
- Handover 相关：
  - `taf.wts.client.gnb_xn_ho_report_param` 文档中出现 source/target gNB、source cell CGI、handover report 等参数，说明 handover 分析可能还需要 WTS/HO report 方向进一步查询。
  - 本次脚本先实现“通过 PA 改变 source/target cell 信号强弱触发 handover”的外部条件编排。
- gNB Wireshark / pcap 抓包：
  - `taf.collectors.ip_traffic_capturing.create_vcu_ip_traffic_capturing_file_collector`
  - `taf.collectors.core.setup_collectors`
  - `taf.collectors.core.start_collectors`
  - `taf.collectors.core.stop_collectors`
  - `taf.collectors.core.collect_collectors`
  - `taf.collectors.core.teardown_collectors`
  - `taf.gnb.oam.coam.cu.start_ip_traffic_capture`
  - `taf.gnb.oam.coam.cu.stop_ip_traffic_capture`
  - CU capture 支持 `capture_type=all|plane|pod`、`measurement_point=NE_Terminated|Transport_Interface`、`plane_type=[uplane,cplane,mplane,others]`。

本次生成的 direct Python 练习文件：

```text
C:\TA\taf_mcp_practise\sbts_handover_pa_wireshark_direct_python.py
```

脚本做了什么：

- 定义 `CellPaConfig` 表示 source/target cell 对应的 PA/attenuator 映射。
- 定义 `HandoverProfile` 表示 source/target attenuation ramp：
  - source cell attenuation 从低变高，让 source 逐渐变弱。
  - target cell attenuation 从高变低，让 target 逐渐变强。
- 定义 `GnbCaptureConfig` 表示 gNB pcap 抓包配置。
- 定义 `GnbCaptureSession` 在 handover 窗口前后自动 start/stop/collect pcap。
- 定义 `PaController` 抽象类，适配不同 PA 类型。
- 实现 `RfAttenuatorController`：
  - 使用 `taf.hw.rf_attenuator`。
  - 支持 JFW fading scenario。
- 实现 `AzimuthChannelEmulatorController`：
  - 预留 `DirectedLink.set_link_atten` 方式。
  - 由于 Azimuth DirectedLink 构造方式依赖目标实验室配置，当前需要在真实环境中补齐 setup。
- 支持 `--dry-run`，用于先检查流程和参数，不真实调用 TAF API。

dry-run 示例：

```powershell
cd C:\TA\taf_mcp_practise
python .\sbts_handover_pa_wireshark_direct_python.py `
  --dry-run `
  --source-cell "NR_CELL_SOURCE" `
  --target-cell "NR_CELL_TARGET" `
  --source-pa-type jfw_rf_attenuator `
  --target-pa-type jfw_rf_attenuator `
  --source-pa-ports 1,2 `
  --target-pa-ports 3,4
```

真实执行时需要补齐：

```powershell
python .\sbts_handover_pa_wireshark_direct_python.py `
  --source-cell "NR_CELL_SOURCE" `
  --target-cell "NR_CELL_TARGET" `
  --source-pa-type jfw_rf_attenuator `
  --target-pa-type jfw_rf_attenuator `
  --source-pa-ip "SOURCE_PA_IP" `
  --target-pa-ip "TARGET_PA_IP" `
  --source-pa-ports 1,2 `
  --target-pa-ports 3,4 `
  --cu-host "CU_OR_VCU_OAM_HOST" `
  --cu-user "Nemuadmin" `
  --cu-password "PASSWORD"
```

验证命令：

```powershell
python .\sbts_handover_pa_wireshark_direct_python.py --help
python .\sbts_handover_pa_wireshark_direct_python.py --dry-run
```

预期结果：

```text
--help 能显示参数。
--dry-run 能打印将要执行的 PA setup、gNB capture start、attenuation ramp、capture stop/collect、PA teardown 步骤。
```

真实环境验证前需要确认：

- `taf.hw.rf_attenuator` 的 direct Python import path 是否与当前 TAF 版本一致。
- `set_ports_attenuation` / `set_ports_fading_attenuation` 的 Python 参数名是否与 Robot keyword wrapper 完全一致。
- source/target PA port 与 source/target cell 的物理映射是否正确。
- PA attenuation 值范围是否符合设备限制。
- CU/VCU OAM host、账号、capture_type、plane_types 是否正确。
- handover 是否需要同时控制 UE attach、measurement report、cell lock/unlock 或 WTS HO report 采集。

常见失败判断：

- `ModuleNotFoundError`：目标 TAF venv 没安装对应 package，或 import path 不一致。
- PA setup 失败：IP、port、vendor/model、端口号或 testline attenuator 配置错误。
- fading scenario 不支持：非 JFW 或设备型号不支持 multi-port fading。
- pcap collector 失败：CU/VCU OAM host、账号、measurement point 或 capture type 不正确。
- handover 未发生：source/target PA 映射错误、attenuation ramp 不够、UE 未处于 source cell、邻区/HO 参数未配置。
