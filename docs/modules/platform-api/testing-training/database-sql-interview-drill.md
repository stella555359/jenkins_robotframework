# 数据库与 SQL 面试专项训练

## 这份文档的目标

这份训练文档只做一件事：

```text
把“数据库会一点”练成“能支撑测试结论和面试表达”。
```

它优先解决下面这些问题：

- 当前仓库里的数据库链路到底怎么理解
- 测试工程师为什么要做数据库校验
- 常见 SQL 在面试里怎么答、怎么用
- 如何把 SQL 查询和接口结果串成一条证据链

## 当前仓库里的数据库练习面

在 `platform-api` 里，最适合练数据库能力的地方是：

- `app/repositories/run_repository.py`
- `app/services/run_service.py`
- `tests/test_runs.py`
- `tests/conftest.py`

这条链路可以压缩成：

```text
API 请求 -> service 组装业务语义 -> repository 访问 SQLite -> 测试再反查 DB 验证
```

## 你现在最应该先理解的 4 个点

### 1. SQLite 在这里存的不是“大文件”，而是平台元数据

当前 `runs` 表存的是：

- `run_id`
- `executor_type`
- `testline`
- `robotcase_path`
- `status`
- `message`
- `enable_kpi_generator`
- `enable_kpi_anomaly_detector`
- `workflow_spec_json`
- `artifact_manifest_json`
- `kpi_summary_json`
- `detector_summary_json`
- `created_at`
- `updated_at`

最短记忆版：

```text
SQLite 这里更像平台账本，不是文件仓库。
```

### 2. repository 层才是数据库访问层

当前最关键的方法：

- `insert_run_record()`
- `list_run_records()`
- `get_run_record_by_id()`
- `update_run_record()`

这层负责：

- 建表
- 插入
- 查询
- 更新
- JSON / 布尔字段的编码和解码

### 3. service 层决定“业务上要怎么查、怎么写”

例如：

- `run_create()` 负责生成 `run_id`
- `get_run_list()` 负责组装列表响应
- `get_run_detail()` 负责处理“查到 / 查不到”
- `apply_run_callback()` 负责把 Jenkins 回调更新进数据库

### 4. 测试工程师要学会“接口结果 + 数据库结果”双校验

不要只看：

- `response.status_code == 200`
- `response.json()["status"] == "created"`

还要看：

- 库里是不是确实有这条记录
- 记录字段和接口返回是否一致

## 为什么测试工程师要会查库

面试里你可以直接用下面这套口径：

### 原因 1：接口返回不一定代表真实落库成功

有些问题会表现成：

- 接口返回成功
- 但数据库没写进去

如果不查库，只看前端或接口响应，可能会误判功能正常。

### 原因 2：查库能帮助定位问题层级

例如：

- 接口返回错，但数据库是对的
  - 说明更可能是返回组装问题
- 接口和数据库都错
  - 说明可能是 service 或 repository 问题
- 接口对，数据库错
  - 说明可能是落库逻辑或更新逻辑有问题

### 原因 3：数据库是很多业务流程的最终证据

尤其是：

- 创建
- 更新
- 状态变更
- 统计
- 列表排序

这些动作，最终都要落到数据层验证。

## 当前仓库里最值得你复述的数据库调用链

### 场景 1：创建 run

```text
POST /api/runs
-> router 接请求
-> RunCreateRequest 校验输入
-> run_create() 组装 record
-> insert_run_record() 写入 SQLite
-> RunCreateResponse 返回给调用方
```

### 场景 2：查询 run 列表

```text
GET /api/runs
-> router 接请求
-> get_run_list()
-> list_run_records()
-> 从 runs 表查出数据
-> service 组装 RunListResponse
-> 返回 JSON
```

### 场景 3：按 run_id 查详情

```text
GET /api/runs/{run_id}
-> router 接请求
-> get_run_detail(run_id)
-> get_run_record_by_id(run_id)
-> 查不到返回 404
-> 查到则组装 RunDetailResponse
```

## 10 组数据库高频训练题

下面这些题，建议你自己先口答，再看“答题方向”。

### 题 1：为什么测试不能只看接口返回？

答题方向：

- 接口返回只是表现层结果
- 数据库才是很多业务动作的真实落点
- 需要确认写入、更新、排序、状态变化是否真的发生

### 题 2：如果 `POST /api/runs` 返回 200，你会怎么验证这次创建真的成功？

答题方向：

- 先看返回体里的 `run_id / status / message`
- 再根据 `run_id` 去数据库查记录
- 核对 `testline / robotcase_path / status`

### 题 3：列表接口为什么也要查数据库？

答题方向：

- 当前列表数据来源就是 `runs` 表
- 如果不查库，只返回假数据，业务可信度会出问题

### 题 4：如果详情接口查不到数据，为什么返回 404 比 `200 + {}` 更合理？

答题方向：

- `404` 语义明确表示资源不存在
- `200 + {}` 容易让调用方误解为查到了，只是字段为空

### 题 5：repository 层和 service 层的区别是什么？

答题方向：

- repository 管 SQL 和数据库访问
- service 管业务语义和调用时机

### 题 6：为什么当前项目里有 JSON 字段还要存在 SQLite 里？

答题方向：

- `workflow_spec_json`、`artifact_manifest_json` 这种结构化元数据需要保存
- 当前阶段用 SQLite 存 JSON 文本足够轻量
- repository 会负责编码和解码

### 题 7：如果接口返回顺序不对，你会先查哪里？

答题方向：

- 先看 repository 的 SQL 是否有 `ORDER BY created_at DESC`
- 再看 service 是否重排过结果
- 最后再看测试数据是否足够区分先后顺序

### 题 8：为什么要做“接口返回值和数据库记录一致性”测试？

答题方向：

- 防止接口是 fake data
- 防止返回字段被错误组装
- 保证列表、详情、回调状态和 DB 真实状态一致

### 题 9：如果遇到主键冲突，测试时该关注什么？

答题方向：

- 是否有重试逻辑
- 是否能生成新的 `run_id`
- 是否会导致写入失败

### 题 10：你会怎么通过数据库帮助定位接口 bug？

答题方向：

- 先复现问题
- 抓请求和返回
- 再查数据库看是否真的写入 / 更新
- 根据“接口和 DB 是否一致”判断问题大概在哪一层

## 10 条 SQL 训练题

下面这些 SQL 先按 `runs` 表来练最有效。

### 1. 查所有 run，按创建时间倒序

```sql
SELECT run_id, testline, robotcase_path, status, created_at
FROM runs
ORDER BY created_at DESC;
```

### 2. 查指定 `run_id` 的详情

```sql
SELECT *
FROM runs
WHERE run_id = 'run-20260423093000000';
```

### 3. 查某个 `testline` 下的所有 run

```sql
SELECT run_id, testline, status, created_at
FROM runs
WHERE testline = 'T813'
ORDER BY created_at DESC;
```

### 4. 统计每个 `testline` 的 run 数量

```sql
SELECT testline, COUNT(*) AS run_count
FROM runs
GROUP BY testline
ORDER BY run_count DESC;
```

### 5. 查开启了 KPI generator 的 run

```sql
SELECT run_id, testline, enable_kpi_generator, created_at
FROM runs
WHERE enable_kpi_generator = 1;
```

### 6. 查状态为 `completed` 的 run

```sql
SELECT run_id, status, finished_at
FROM runs
WHERE status = 'completed';
```

### 7. 查 message 为空字符串的异常数据

```sql
SELECT run_id, status, message
FROM runs
WHERE message = '';
```

### 8. 查某个时间之后创建的 run

```sql
SELECT run_id, created_at
FROM runs
WHERE created_at >= '2026-04-23T09:00:00+08:00'
ORDER BY created_at DESC;
```

### 9. 统计每种状态的 run 数量

```sql
SELECT status, COUNT(*) AS status_count
FROM runs
GROUP BY status;
```

### 10. 查同时开启 generator 和 detector 的 run

```sql
SELECT run_id, testline, enable_kpi_generator, enable_kpi_anomaly_detector
FROM runs
WHERE enable_kpi_generator = 1
  AND enable_kpi_anomaly_detector = 1;
```

## SQL 题不只要会写，还要会解释

面试时不要只报出 SQL。

更推荐你用这种结构回答：

1. 我先明确我要验证什么
2. 我会查哪张表、哪些字段
3. 我为什么要这样加条件
4. 查询结果出来后，我怎么判断功能是否正常

例如：

```text
如果我要验证 POST /api/runs 是否真的创建成功，我会先根据接口返回的 run_id 去 runs 表查这条记录，重点核对 testline、robotcase_path、status 是否和请求及返回值一致。这样可以确认接口不是只返回成功，而是真的完成了落库。
```

## 当前仓库里最推荐你看的代码文件

- `platform-api/app/repositories/run_repository.py`
- `platform-api/app/services/run_service.py`
- `platform-api/tests/test_runs.py`
- `platform-api/tests/conftest.py`

## 最小自测清单

练完这份文档后，至少确认自己能回答下面 6 个问题：

- [ ] 为什么测试工程师要会查数据库
- [ ] repository 和 service 的职责边界是什么
- [ ] 创建成功后你会怎么查库验证
- [ ] 列表接口为什么也要查数据库
- [ ] `404` 为什么比 `200 + {}` 更合理
- [ ] 你能写出至少 5 条常见 SQL，并解释用途

## 相关文档

- [1 周测试岗面试训练总览](interview-1week-test-engineer-training.md)
- [测试全流程表达与工具位置图](test-process-and-tool-mapping.md)
- [Testing Workflow](../guides/testing-workflow.md)
