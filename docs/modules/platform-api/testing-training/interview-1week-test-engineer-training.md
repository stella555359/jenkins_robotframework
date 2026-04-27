# 1 周测试岗面试训练总览

## 这份文档的目标

这不是业务实现 step，也不是一份泛泛的学习清单。

它的目标现在进一步收敛成一条更适合面试的主线：

- 用 1 周时间，围绕测试工程师 JD 做最小但高收益的面试准备
- 不再只做零散的 `Postman / SQL / JMeter` 练习，而是优先做一条真实闭环
- 把当前 `jenkins_robotframework` 仓库当成你面试里的项目案例，而不是重新开一个练习项目

## 这一周的主线判断

这一周最值得你优先完成的，不是把所有工具都学深，而是把下面这条链路讲清、看清、尽量跑清：

```text
platform-api -> Jenkins -> Robot -> callback -> SQLite
```

这样做的好处是：

- 面试时你能讲“完整执行链”，不只是讲工具按钮
- 你能同时覆盖接口测试、数据库校验、自动化调度、结果回写
- 你的项目叙述会更完整，更像真实测试平台

这一周的取舍固定为：

- 主任务：`platform-api -> Jenkins -> Robot -> callback -> DB`
- 必做辅助：`Postman + SQL + JMeter` 最小训练
- 可选加分：`automation-portal` 超薄展示层
- 先放后面：`test-workflow-runner`

## 这份 JD 真正在要什么

从能力要求看，这份岗位更像：

```text
业务测试 + 接口测试 + 数据校验 + 一点自动化意识
```

不是纯手工点点点，也不是纯性能测试岗，更不是纯自动化开发岗。

你最需要补的 4 块能力是：

### 1. 测试全流程表达能力

你需要能讲清：

- 需求分析
- 测试点拆解
- 用例设计
- 测试执行
- 缺陷跟踪
- 回归测试
- 上线前后保障

### 2. 数据库校验能力

你需要能讲清：

- 为什么测试不能只看接口返回
- 如何用 SQL 验证业务结果
- 如何通过查库定位问题到底在接口层、服务层还是数据层

### 3. 接口测试与执行链理解能力

你需要能讲清：

- 怎么设计 happy path / failure path
- 怎么看状态码、响应体、错误语义
- 怎么把 `run -> callback -> DB` 串成一条验证链
- Postman 在接口测试里到底解决什么问题

### 4. AI 辅助测试与工具认知能力

你不需要 1 周内把工具都学深，但至少要会解释：

- `XMind` 用来做测试点拆解和脑图整理
- `Postman` 用来做接口调试、接口校验、场景串联
- `JMeter` 用来做最小性能认知和基础压测
- `Cursor / AI` 用来辅助生成草稿、补测试点、分析日志，但最终断言和边界要自己复核

## 这一周最合理的学习顺序

按当前时间约束，优先顺序建议固定成：

1. 先把真实闭环主线固定成面试故事
2. 再用 `Postman + SQL` 把接口和数据库证据链练熟
3. 再补测试全流程口语表达和排障说法
4. `JMeter` 只做到“会解释 + 做过最小 smoke”
5. `automation-portal` 只有在前面稳定后才考虑补超薄展示层

原因很简单：

- 面试时“真实链路 + 证据链”比零散工具更有说服力
- 你已经有 Jenkins 和真实 Robot case 条件，应该优先利用
- 你只有 1 周，最怕把时间花在前端细节或低收益的深度工具学习上

## 1 周训练日程

### Day 1：冻结面试主线

目标：

- 先把“我要讲什么项目”固定下来

最少要完成：

- 用自己的话讲清 `platform-api -> Jenkins -> Robot -> callback -> SQLite`
- 看懂 `platform-api/app/api/v1/router.py`、`platform-api/app/services/run_service.py`、`platform-api/app/repositories/run_repository.py`
- 回看 [Step 11：打通 Jenkins trigger / callback 最小闭环](../steps/step-11-jenkins-trigger-and-callback.md)
- 写 1 版 2 分钟项目介绍

### Day 2：先把 API 和数据库证据链打稳

目标：

- 用真实 `run` 数据把“创建 -> 查列表 -> 查详情”走通

最少要完成：

- 练 `POST /api/runs`
- 练 `GET /api/runs`
- 练 `GET /api/runs/{run_id}`
- 用 SQL 反查 `runs` 表，确认接口结果和数据库一致
- 开始用 Cursor 辅助生成第一版 Postman 断言和 SQL 查询草稿

### Day 3：接 Jenkins 和真实 Robot case

目标：

- 让这周的主线从“半真实”变成“真实闭环”

最少要完成：

- 用已有 Jenkins 和正常 Robot case 跑一次真实执行
- 让 Jenkins 带着真实 `run_id` 回调 `POST /api/runs/{run_id}/callbacks/jenkins`
- 验证 `status / jenkins_build_ref / 时间戳` 已真实写回
- 再用 SQL 验证一次回调后的数据库状态

### Day 4：补失败路径和排障话术

目标：

- 不只会讲成功路径，还要会讲测试和排障

至少覆盖下面 4 类场景：

- 创建成功但回调未发生
- 回调字段不完整
- `run_id` 不存在时回调失败
- Jenkins / Robot 执行失败但平台要能留下状态痕迹

### Day 5：把工具和证据链串起来

目标：

- 用工具支撑你的测试结论，而不是只会报工具名

最少要完成：

- 用 Postman 跑一轮真实闭环接口顺序
- 用 SQL drill 验证一次真实落库结果
- 把“接口结果 + DB 结果 + Jenkins 结果”讲成一条证据链
- 整理“测试全流程 + 接口测试 + 数据库校验”的口语稿

### Day 6：JMeter 最小认知 + 可选薄展示层

目标：

- 只补最小性能认知，不让它吃掉主线时间

当前只建议做：

- 一个最小 `GET /api/health` 压测
- 一个最小 `GET /api/runs` 查询压测

如果前 5 天都稳定了，再决定是否加一层极薄的 `automation-portal` 展示，只做：

- run 提交
- run list
- run detail

如果主线还不稳，这一天直接继续补主线，不勉强做前端。

### Day 7：模拟面试

目标：

- 把前 6 天的动作输出成可复述能力

至少要练 5 类问题：

- 你做过什么完整自动化测试项目
- 你怎么做数据库校验
- 你怎么做接口测试
- 你如何定位 Jenkins / 接口 / DB 问题
- 你如何使用 AI 辅助 Postman、SQL、JMeter 和日志分析

## 当前仓库里最适合拿来练什么

这一周不建议你把重点放在 `test-workflow-runner`。

对这次面试准备来说，当前更适合重点使用：

- `platform-api`
- 你现有的 Jenkins 环境
- 你现有的真实 Robot case

原因：

- 有现成 API
- 有现成 SQLite 持久化
- 有 pytest
- 有真实的 repository / service / router 分层
- 很适合练“接口 + 数据库 + 测试设计”
- 真实 Jenkins 和真实 Robot case 会让你的项目故事更完整
- `automation-portal` 当前还是占位，不适合这一周当主线

### 当前最值得看的代码入口

- `platform-api/app/api/v1/router.py`
- `platform-api/app/services/run_service.py`
- `platform-api/app/repositories/run_repository.py`
- `platform-api/tests/test_runs.py`
- `platform-api/tests/conftest.py`

## 这轮训练的输出物

这 1 周结束后，至少应该沉淀出下面 6 样东西：

1. 一份“真实闭环”项目讲述稿
2. 一份数据库常见题和 SQL 练习清单
3. 一份接口测试清单
4. 一份测试全流程口语稿
5. 一份 Postman 最小练习资产
6. 一份 AI 辅助测试方法总结

## 当前最重要的判断原则

这 1 周最重要的不是：

- 工具点得多熟
- 前端页面做得多完整
- 术语背得多花

而是：

```text
你能不能把真实执行链、接口行为、数据库证据、排障路径和 AI 提效方法讲清楚。
```

## AI 如何放进这一周

这周不是把 AI 当成“自动替你测试”的黑盒，而是把它当成高效率助手。

你可以这样使用：

- 让 AI 帮你起草 Postman 请求和断言
- 让 AI 帮你起草 SQL 查询和数据校验思路
- 让 AI 帮你生成 JMeter smoke 的最小参数建议
- 让 AI 帮你阅读 Jenkins / 接口失败日志，缩小排查范围

但你必须自己复核：

- 接口路径和字段名是否真实存在
- SQL 是否真的对应当前表结构
- 断言是否真的符合业务语义
- 边界值和失败场景是否被漏掉

详细方法见：

- [AI 辅助 API / DB / JMeter / 日志分析方法](ai-assisted-api-and-db-testing.md)

## 相关训练材料

- [数据库与 SQL 面试专项训练](database-sql-interview-drill.md)
- [测试全流程表达与工具位置图](test-process-and-tool-mapping.md)
- [AI 辅助 API / DB / JMeter / 日志分析方法](ai-assisted-api-and-db-testing.md)
- [Testing Workflow](../guides/testing-workflow.md)
