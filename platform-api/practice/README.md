# Platform API Practice Assets

## 目录定位

这里放的是围绕 `platform-api` 做测试面试训练的轻量练习资产。

当前目标不是把这些工具深度接进主业务链，而是先给你一套：

- 能看
- 能跑
- 能拿来解释测试流程

的最小练习面。

对这一周面试准备来说，推荐你把这些资产放进下面这条主线里使用：

```text
POST /runs -> GET /runs -> GET /runs/{run_id} -> Jenkins callback -> SQL 反查 -> JMeter 最小 smoke
```

## 当前资产

### `postman/`

用于接口测试和最小业务链路串联。

当前文件：

- `platform-api-interview-practice.collection.json`
- `platform-api-local.environment.json`

推荐顺序：

1. `GET /health`
2. `POST /runs`
3. `GET /runs`
4. `GET /runs/{run_id}`
5. `POST /runs/{run_id}/callbacks/jenkins`
6. `GET /runs/{run_id}/artifacts`
7. `GET /runs/{run_id}/kpi`

### `sql/`

用于数据库与 SQL 面试训练。

当前文件：

- `run-api-sql-drill.sql`

推荐用途：

- 跟接口返回一起做 DB 验证
- 练常见查询、统计、条件筛选
- 练“为什么要查库”的面试表达

### `jmeter/`

用于 JMeter 最小认知和轻量试跑。

当前文件：

- `platform-api-health-and-runs-smoke.jmx`

当前只建议用来压：

- `GET /api/health`
- `GET /api/runs`

## 建议使用顺序

如果你时间很紧，固定按下面顺序练最划算：

1. 先跑 `postman/` 里的 `health -> create -> list -> detail`
2. 再补 `callbacks/jenkins`，把 run 状态回写这一步看懂
3. 再跑 `sql/`，把数据库校验练熟
4. 最后只用 `jmeter/` 做一轮最小认知
5. `automation-portal` 只有在主线稳定后才考虑补展示，不放进这里当主任务

## 每一步可以向 Cursor 提什么

### 跑 `postman/` 之前

可以问：

- “请根据当前 `platform-api` 接口，帮我整理一轮最小真实闭环的 Postman 执行顺序。”
- “请检查这份 collection 的断言是否只验证了状态码，是否缺少业务字段断言。”

### 跑 `sql/` 之前

可以问：

- “请根据 `runs` 表和当前 run API，帮我起草创建后查库、回调后查库、一致性校验的 SQL。”
- “请帮我解释这些 SQL 分别在验证什么测试结论。”

### 跑 `jmeter/` 之前

可以问：

- “请基于当前 `.jmx`，帮我解释线程数、循环数、ramp-up 的含义，并给一个保守 smoke 建议。”
- “请检查这份 JMeter 计划是否只压了 `health` 和 `runs`，有没有超出当前一周范围。”

### 看 Jenkins / 接口失败日志时

可以问：

- “这是 Jenkins callback 失败日志，请帮我先按接口层、数据库层、Jenkins 层拆分排查路径。”
- “这是一次 run 详情和数据库结果，请帮我判断更像是 callback 没到、字段没回写，还是查询接口没读对。”

最重要的前提是：

```text
让 AI 先给你草稿和排查方向，但最终字段、断言、SQL 和结论都要自己复核。
```

## 配套训练文档

- `docs/modules/platform-api/testing-training/interview-1week-test-engineer-training.md`
- `docs/modules/platform-api/testing-training/database-sql-interview-drill.md`
- `docs/modules/platform-api/testing-training/test-process-and-tool-mapping.md`
- `docs/modules/platform-api/testing-training/ai-assisted-api-and-db-testing.md`
