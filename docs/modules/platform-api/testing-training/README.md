# Platform API Testing Training

## 目录定位

这里放的是 `platform-api` 相关的测试训练材料。

和 `testing-automation/` 不同，这里优先回答：

- 这一轮该怎么训练测试思维
- 当前最值得补哪类测试能力
- 面试场景下应该怎么讲清测试流程、接口测试、数据库校验
- `XMind / Postman / JMeter / SQL` 在测试流程里分别放哪里

最短记忆版：

```text
testing-training = 训练思维、补方法、做面试准备
testing-automation = 记录这一轮已经自动化了什么
```

## 当前推荐入口

如果你现在是为了补“测试工程师岗位面试能力”，优先看下面几份：

1. [1 周测试岗面试训练总览](interview-1week-test-engineer-training.md)
2. [数据库与 SQL 面试专项训练](database-sql-interview-drill.md)
3. [测试全流程表达与工具位置图](test-process-and-tool-mapping.md)
4. [AI 辅助 API / DB / JMeter / 日志分析方法](ai-assisted-api-and-db-testing.md)

如果你想回看已有 step 训练文档，再看：

- [Step 9 Test Training](step-09-test-training.md)

## 当前训练主线

在这轮面试准备里，优先顺序固定为：

1. 先固定 `platform-api -> Jenkins -> Robot -> callback -> DB` 这条真实闭环主线
2. 再用 `Postman + SQL` 把接口和数据库证据链练熟
3. 再补“测试全流程”口语表达和排障说法
4. 最后只做最小 `JMeter` 认知和轻量试跑
5. `automation-portal` 只作为可选薄展示层，不作为本周主线

## 配套练习资产

这轮训练对应的可执行练习资产，统一放在：

- `platform-api/practice/`

后续优先使用：

- `platform-api/practice/postman/`
- `platform-api/practice/sql/`
- `platform-api/practice/jmeter/`

## 相关文档

- [Testing Workflow](../guides/testing-workflow.md)
- [Platform API 学习总索引](../index.md)
- [Step 9 Test Automation](../testing-automation/step-09-test-automation.md)
