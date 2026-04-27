# 8 天全项目执行计划

## 文档定位

这份文档是当前 `C:\TA\jenkins_robotframework` 的执行计划和恢复入口。

Cursor 重启或新会话后，先按下面顺序恢复上下文：

1. `docs/README.md`
2. `docs/overview/roadmap.md`
3. 本文件
4. 当前模块的 `README.md` 和 `index.md`
5. 当前正在执行的 step 文档

## 当前执行状态

- 当前计划：8 天全项目收口计划
- 当前天数：Day 1
- 当前模块：`platform-api`
- 当前小 step：Step 11：打通 Jenkins trigger / callback 最小闭环
- 当前状态：Step 11 已补 callback 不存在 `run_id` 的 pytest、学习版说明和 testing-automation 记录，验证命令等待用户在服务器上执行
- 当前重要约定：AI 不主动执行 pytest / Allure / Postman / JMeter / 前端测试等验证命令，只提供验证步骤和预期结果

## 总目标

8 天后完成一个真实可演示、可测试、可复盘的纵向闭环：

```text
automation-portal
  -> platform-api
  -> Jenkins
  -> UTE Robot
  -> result / artifacts / KPI
  -> callback
  -> SQLite
  -> portal detail / KPI / artifact 展示
```

## 完成口径

- `platform-api`
  - 完成 run contract、Jenkins callback、artifact/KPI 查询、execution-ready detail。
- `jenkins-kpi-platform`
  - 完成 runner dry-run、真实 Jenkins/Robot/UTE 触发参数、result/timeline/artifact manifest、generator/detector 内部接入验证。
- `automation-portal`
  - 完成 React 门户，包括 run submission、workflow builder、run list、run detail、KPI summary、artifact/detector 报告入口。
- 测试流程
  - 覆盖需求拆解、用例设计、API 自动化、DB 校验、接口联调、前端测试、JMeter smoke、Allure HTML 报告展示、回归清单。
- AI 辅助自动化测试
  - 用于测试点生成、pytest/Playwright 用例草稿、Postman 断言审查、SQL 校验设计、日志/失败分析、测试报告总结。

暂时搁置：

- `docs/modules/platform-api/testing-training/interview-1week-test-engineer-training.md`

这份面试训练文档不删除，后续作为专项练习资料。

## 协作模式

每天固定按同一套节奏走：

1. 先读当天 step 文档和相关代码，确认“今天完成什么、不做什么”。
2. 先画接口/流程边界，再开始改代码。
3. 每完成一个小能力，AI 只整理服务器验证命令、预期结果和失败判断方式。
4. 用户在服务器上执行验证，把结果贴回来。
5. AI 根据验证结果继续修复或进入下一步。
6. 每天结束前更新 step 文档、testing-automation 记录和演示命令。

## 每个小 Step 的教学式交付标准

每个小 step 完成后，必须留下学习版说明，不能只交代码。

固定交付：

1. 这一步解决的问题
2. 改了哪些文件
3. 核心调用链
4. 关键字段解释
5. 服务器验证命令和预期结果
6. 需要用户确认的业务点
7. 小结和复盘问题

学习版说明优先写入对应 step 文档末尾。

测试证据和自动化说明写入对应模块的 `testing-automation/`。

## Day 1：Platform API 主链路

目标：

完成 `platform-api` Step 10-13：

- Step 10：冻结 executor-agnostic run contract
- Step 11：打通 Jenkins trigger / callback 最小闭环
- Step 12：补齐 artifact / KPI / detector metadata 查询面
- Step 13：把 run detail 升级为 execution-ready 详情入口

重点文件：

- `platform-api/app/schemas/run.py`
- `platform-api/app/services/run_service.py`
- `platform-api/app/repositories/run_repository.py`
- `platform-api/app/api/v1/router.py`
- `platform-api/tests/test_runs.py`

Day 1 验收由用户在服务器执行：

```bash
cd /path/to/jenkins_robotframework/platform-api
python -m pytest tests/test_runs.py
python -m pytest tests/test_runs.py --alluredir=allure-results
```

当前 Day 1 / Step 10 进展：

- 已确认 `RunCreateRequest` 支持 `robot` 和 `python_orchestrator`。
- 已确认 service 层存在 `_validate_run_create_request()`。
- 已确认 `python_orchestrator` 缺少 `workflow_spec` 已有测试。
- 已新增 `robot` 缺少 `robotcase_path` 的测试：
  - `test_create_robot_run_requires_robotcase_path`
- 已按 review 调整字段边界：
  - 真正共用字段：`testline`、`executor_type`、`build`
  - `robot` 字段：`robotcase_path`
  - `python_orchestrator` 字段：`workflow_spec`
  - KPI 后处理字段：`enable_kpi_generator`、`enable_kpi_anomaly_detector`、`kpi_config`
  - 扩展字段：`metadata`
- 已从 create request contract 移除顶层 `scenario` / `workflow_name`
- 已新增 `robot` 模式拒绝 KPI 后处理配置的测试：
  - `test_create_robot_run_rejects_kpi_options`
- 已更新 Step 10 学习版说明：
  - `docs/modules/platform-api/steps/step-10-executor-agnostic-run-contract.md`
- 已新增 Step 10 testing-automation 记录：
  - `docs/modules/platform-api/testing-automation/step-10-test-automation.md`
- 已由用户在服务器验证通过。
- Step 10 只要求 `allure-results` 原始目录产出。
- Jenkins 中展示 Allure HTML 报告放入后续 Jenkins / 测试流程收口。

## Day 2：Jenkins KPI Platform 执行层

目标：

完成 runner、Jenkins/Robot/UTE 接入参数、result/artifact manifest、generator/detector 接入验证。

重点文件：

- `jenkins-kpi-platform/gnb_kpi_orchestrator/models.py`
- `jenkins-kpi-platform/gnb_kpi_orchestrator/request_loader.py`
- `jenkins-kpi-platform/gnb_kpi_orchestrator/runner.py`
- `jenkins-kpi-platform/gnb_kpi_orchestrator/result_builder.py`
- `jenkins-kpi-platform/gnb_kpi_orchestrator/handlers/kpi_generator.py`
- `jenkins-kpi-platform/gnb_kpi_orchestrator/handlers/kpi_detector.py`

需要固定：

- Jenkins base URL、job name、credential 引用
- UTE 节点标签或目标机器
- Robot workspace、case path、variables、outputdir
- run_id、callback URL、artifact archive path
- `dry_run` 和 `jenkins_robot` 两种执行模式
- Jenkins Allure Publisher 配置：
  - pytest 产出 `allure-results`
  - Jenkins job 归档并展示 Allure HTML 报告
  - Robot 原生 `log.html` / `report.html` 作为 artifact 链接展示

## Day 3：真实 Jenkins/Robot 回写闭环

目标：

打通：

```text
React/API -> Jenkins -> UTE Robot -> callback -> DB -> portal detail
```

需要验证：

- Robot 成功执行
- Robot 执行失败
- UTE 不可达
- artifact 缺失
- callback 失败

## Day 4：Automation Portal 基础工程

目标：

建立 React + Vite + TypeScript 基础工程、API client、layout、路由和基础测试框架。

页面骨架：

- run submit
- workflow builder
- run list
- run detail

## Day 5：Automation Portal 核心页面

目标：

完成：

- `RunSubmit`
- `RobotRunForm`
- `WorkflowBuilder`
- `RunList`
- `RunDetail`
- `KpiSummary`
- `ArtifactLinks`

完成后，用户应能通过 portal 创建真实 Robot case run，也能创建带并行 stage/item 的 KPI workflow。

## Day 6：Portal 联调、体验和质量补齐

目标：

补齐：

- 加载态
- 空状态
- 错误态
- 表单校验
- API 错误展示
- callback 前后的状态刷新
- artifact/KPI 空数据展示
- Robot 失败时的 detail 展示

## Day 7：完整测试流程和 AI 辅助自动化测试

测试流程：

1. 需求分析
2. 测试点拆解
3. 用例设计
4. 自动化实现
5. 接口联调
6. 数据验证
7. 性能 smoke
8. 缺陷记录与回归

AI 辅助测试范围：

- 测试矩阵生成
- pytest 草稿生成
- Postman 断言审查
- SQL 校验点设计
- 日志失败分析
- 回归清单生成
- 测试总结生成

## Day 8：文档、演示和回归收口

目标：

更新三模块文档、testing-automation 记录、最终演示脚本和回归清单。

最终演示脚本：

```text
启动 API
  -> 启动 portal
  -> 创建真实 Robot run
  -> Jenkins 在 UTE 执行 Robot
  -> callback 回写
  -> portal 查看详情 / KPI / artifact
  -> 用户执行 pytest / Postman / SQL / JMeter / 前端测试回归
  -> Jenkins 展示 Allure HTML 报告
```

## 后续维护约定

- 每完成一个小 step，更新本文件的“当前执行状态”。
- 每完成一天，更新对应 Day 的完成情况。
- 不在聊天里单独保存关键进度，关键进度必须落到 `docs/`。
