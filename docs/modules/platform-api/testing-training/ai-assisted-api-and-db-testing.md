# AI 辅助 API / DB / JMeter / 日志分析方法

## 这份文档的目标

这份文档只做一件事：

```text
把“我会用 Cursor”讲成一套可执行、可复核、可面试表达的方法。
```

它不是在教你把测试完全交给 AI，而是帮你建立下面这套工作方式：

```text
AI 先给草稿和方向
-> 你用当前仓库和真实结果做核对
-> 最后再把结论沉淀成测试证据和面试说法
```

## 这一周最适合让 AI 介入的 4 个场景

在当前仓库里，AI 最适合辅助你做下面 4 类事：

1. 帮你起草 `Postman` 请求和断言
2. 帮你起草 `SQL` 校验语句和查库思路
3. 帮你起草 `JMeter` smoke 的最小参数建议
4. 帮你分析 `Jenkins / API / DB` 失败日志

当前不建议让 AI 直接替你做的事：

- 直接替你下最终测试结论
- 不经复核就采纳它生成的断言
- 不经核对就执行它生成的写库 SQL
- 不经验证就相信它给出的根因判断

## 一条总原则

你可以强行记这一句：

```text
AI 负责先帮我变快，我自己负责保证结论是真的。
```

## 1. AI 辅助 `Postman`

### 最适合让 AI 帮你的动作

- 根据接口路径起草第一版请求顺序
- 根据返回结构起草 `pm.test(...)` 断言
- 帮你梳理变量依赖，比如 `run_id` 应该从哪个请求保存
- 帮你补“成功路径之外还应测什么”

### 当前仓库里最适合配合使用的文件

- `platform-api/practice/postman/platform-api-interview-practice.collection.json`
- `platform-api/practice/postman/platform-api-local.environment.json`
- `platform-api/app/api/v1/router.py`
- `platform-api/app/services/run_service.py`

### 推荐提问方式

你可以直接问：

```text
请基于当前 platform-api 的 run 接口，帮我检查这份 Postman collection 的请求顺序是否适合真实闭环训练。
```

```text
请根据 POST /api/runs、GET /api/runs、GET /api/runs/{run_id}、POST /api/runs/{run_id}/callbacks/jenkins，
帮我补一版更像面试场景的 Postman 断言草稿，重点关注 run_id、status、message 和 callback 后状态变化。
```

```text
请帮我列出这套接口最容易漏掉的失败场景，但不要编造不存在的字段。
```

### 你自己必须复核的 5 件事

1. 接口路径是否真实存在
2. 字段名是否和当前接口返回一致
3. 断言是不是只测了 `200`，却没测业务字段
4. 是否真的覆盖了失败路径
5. 变量传递是否真的拿到了正确的 `run_id`

### 最推荐的工作方式

```text
先让 AI 起草
-> 再对照 router / service / practice collection 核字段
-> 再自己删掉多余断言
-> 最后再执行
```

## 2. AI 辅助 `SQL`

### 最适合让 AI 帮你的动作

- 根据测试目标起草第一版 `SELECT` 查询
- 帮你把“接口结果”和“数据库结果”对应起来
- 帮你解释每条 SQL 在验证什么结论
- 帮你把排查路径拆成“接口层 / 服务层 / 数据层”

### 当前仓库里最适合配合使用的文件

- `platform-api/practice/sql/run-api-sql-drill.sql`
- `platform-api/app/repositories/run_repository.py`
- `platform-api/tests/test_runs.py`
- `docs/modules/platform-api/testing-training/database-sql-interview-drill.md`

### 推荐提问方式

```text
请基于 runs 表和当前 run API，帮我起草 3 类 SQL：
1. 创建后查库
2. callback 后查库
3. 列表与详情一致性校验
只使用查询语句，不要生成 delete/update。
```

```text
请解释下面这条 SQL 在测试里到底证明了什么，如果查不到记录，最可能先怀疑哪一层。
```

```text
如果 POST /api/runs 返回成功，但数据库里查不到 run_id，请帮我给出一个接口层 -> service 层 -> repository 层的排查顺序。
```

### 你自己必须复核的 5 件事

1. 表名和列名是否真实存在
2. 查询条件是否真的对应当前 `run_id`
3. 查询结果是否真的支持你的测试结论
4. AI 有没有把 JSON 字段、布尔字段理解错
5. 是否严格限制在只读查询范围内

### 当前阶段的安全边界

这一周训练里，最推荐你让 AI 帮的是：

- `SELECT`
- `COUNT`
- `ORDER BY`
- 条件筛选

这一周不建议让 AI 直接帮你执行或生成：

- `DELETE`
- `UPDATE`
- 改表语句

## 3. AI 辅助 `JMeter`

### 最适合让 AI 帮你的动作

- 解释当前 `.jmx` 的线程数、循环数、ramp-up
- 根据“最小 smoke”目标给出更保守的参数建议
- 帮你区分“功能测试”和“性能测试”的表达边界
- 帮你整理压测后应该看哪些基础指标

### 当前仓库里最适合配合使用的文件

- `platform-api/practice/jmeter/platform-api-health-and-runs-smoke.jmx`
- `platform-api/practice/README.md`

### 推荐提问方式

```text
请基于当前 jmeter 脚本，解释线程数、循环次数、ramp-up 分别在控制什么，
并给我一版更保守的 smoke 建议，前提是不影响当前真实环境。
```

```text
请检查这份 jmeter 计划是否只覆盖了 /api/health 和 /api/runs，
如果它开始压复杂链路，请提醒我超出当前一周范围。
```

### 你自己必须复核的 4 件事

1. 压的接口是不是当前该压的最小接口
2. 并发参数是否过大
3. 结果解读是不是被误讲成了功能正确
4. 当前目标是不是 smoke，而不是完整性能评估

## 4. AI 辅助日志分析

### 最适合让 AI 帮你的动作

- 先按层级拆问题：Jenkins、接口、数据库、配置
- 根据报错片段缩小排查范围
- 帮你生成“下一步该查什么”的清单
- 帮你把排障过程整理成面试里的问题定位故事

### 推荐输入给 AI 的信息

最好一次给这些材料：

- Jenkins console 关键报错片段
- 当前 `run_id`
- `GET /api/runs/{run_id}` 的关键返回
- 对应 SQL 查询结果

### 推荐提问方式

```text
这是 Jenkins callback 失败日志，这是 run detail 返回，这是数据库查询结果。
请先不要直接下最终结论，先按 Jenkins 层、API 层、DB 层给我一个排查顺序。
```

```text
如果 run 状态没有更新，哪些情况更像是 callback 没到，哪些情况更像是 callback 到了但字段没正确写入？
```

### 你自己必须复核的 4 件事

1. AI 给的根因是否有真实日志支持
2. 是否已经排除网络、权限、参数问题
3. 接口结果和数据库结果是否互相印证
4. 最终结论能不能回到代码或日志证据上

## 5. 一条最推荐的实战流程

把这一周的 AI 使用固定成下面这条顺序最稳：

1. 先自己明确本轮测试目标  
   例如：我要验证 `run` 创建、列表、详情、callback 回写是否一致。

2. 让 AI 起草第一版草稿  
   例如：Postman 断言、SQL 查询、JMeter smoke 参数、日志排查顺序。

3. 用当前仓库和真实结果做核对  
   重点核：
   - `router.py`
   - `run_service.py`
   - `run_repository.py`
   - Postman collection
   - 数据库查询结果

4. 自己删掉不靠谱的部分  
   比如：
   - 编造的字段
   - 过度复杂的断言
   - 超出当前范围的压测建议
   - 没证据支撑的根因推断

5. 最后再输出测试结论和面试说法

## 6. 面试时怎么讲这件事

最推荐的说法是：

```text
我会用 Cursor 辅助生成 Postman 用例、JMeter smoke 脚本、SQL 校验语句和失败日志分析，但我不会直接照搬。我会自己核对接口字段、数据库结构、断言语义和测试边界，保证 AI 只是提效工具，不替代我的测试判断。
```

如果对方继续追问“你具体怎么做”，你可以继续补：

```text
比如我在当前项目里，会先让 AI 帮我起草 run 接口的 Postman 断言和 runs 表的查询语句，再结合真实 run_id、接口返回和数据库结果去复核。如果 Jenkins callback 失败，我也会把日志、run 详情和 SQL 结果一起给 AI，先让它帮我缩小排查范围，再由我自己确认最终根因。
```

## 7. 最容易踩的坑

- 让 AI 编造不存在的字段和接口
- 只看 AI 生成的断言，不看真实返回
- 只看接口成功，不查数据库
- 只看日志猜原因，不回到代码或数据验证
- 把 AI 说法直接当成面试标准答案，结果被追问细节时接不住

## 最短记忆版

```text
AI 可以帮我更快开始，但不能替我做最终判断。
```

## 相关训练材料

- [1 周测试岗面试训练总览](interview-1week-test-engineer-training.md)
- [数据库与 SQL 面试专项训练](database-sql-interview-drill.md)
- [测试全流程表达与工具位置图](test-process-and-tool-mapping.md)
