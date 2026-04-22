# Platform API Design And Flow

## 文档目标

这份文档专门记录 `platform-api` 当前阶段最容易混的设计点：

- `router / service / repository / core` 各自做什么
- schema 在请求和响应链路里到底什么时候参与
- 为什么后续统一采用“service 直接返回 schema，router 直接 return”
- 为什么列表接口和详情接口要分开

如果你后面再遇到“调用链顺序感混乱”的问题，优先看这份文档。

## 当前分层职责

### `router`

职责：

- 接 HTTP 请求
- 收 path / query / body 参数
- 调用 service
- 返回结果

不建议在这里做：

- SQL 细节
- 业务规则判断
- 数据持久化细节

### `service`

职责：

- 组织业务语义
- 生成服务端字段
- 决定“查到/查不到”“创建成功/失败”这类业务结果
- 组装响应 schema

例如现在 `run_service` 负责：

- 生成 `run_id`
- 生成 `status / message`
- 处理详情接口查不到时的 `404`

### `repository`

职责：

- 只和数据库打交道
- 建表
- 插入
- 查询
- 更新

最短记忆版：

```text
repository 负责“怎么查、怎么写库”，不负责“业务上为什么这样查、这样写”。
```

### `core`

职责：

- 放全局基础能力
- 配置
- 后续可能的日志、异常、常量

当前最典型的文件：

- `platform-api/app/core/config.py`

## schema 在链路里的顺序

最短记忆版：

```text
输入 schema：请求进来时检查
输出 schema：service 返回时组装
response_model：响应出去前再约束一次
```

### 以 `POST /api/runs` 为例

可以把这条链路理解成：

```text
进门检查一次，service 里整理一次，出门前再核对一次
```

顺序是：

1. 请求进来
2. `RunCreateRequest` 先校验输入
3. `service` 做业务处理
4. `service` 组装 `RunCreateResponse`
5. FastAPI 按 `response_model` 再做输出约束

## 为什么 `health` 和 `runs` 的 return 写法不一样

当前：

- `health_service` 返回的是 `dict`
- `run_service` 返回的是 schema 实例

所以会有两种写法：

```python
# health
return HealthResponse(**get_health_payload())

# runs
return run_create(request)
return get_run_list()
```

后续默认统一采用第二种：

```text
service 负责把结果组装成 schema，router 只负责直接 return。
```

`GET /api/health` 当前保持原样，不为了风格统一专门去改它。

## 为什么列表和详情要分开

### `GET /api/runs`

职责：

- 回答“当前有哪些 run”
- 适合列表页
- 支持后续分页、筛选、排序扩展

### `GET /api/runs/{run_id}`

职责：

- 回答“这一条 run 到底是什么”
- 按 `run_id` 精确查单条记录
- 适合详情页和后续产物 / KPI 扩展

最短记忆版：

```text
列表接口解决“有哪些”，详情接口解决“这一条是什么”。
```

## 为什么详情查不到要返回 `404`

因为这类问题的语义不是“字段为空”，而是：

```text
这个 run_id 对应的资源不存在。
```

所以当前正确表达是：

- `404`
- `{"detail": "Run not found."}`

不推荐：

- `200 + {}`

## 当前 `run_id` 语义

当前规则：

- 默认先尝试 `run-时间戳`
- 如果写库冲突，再尝试 `-01 / -02`
- 使用 `CST`（`Asia/Shanghai`）

设计目标：

- 保持可读性
- 避免随机后缀太难排查
- 在极少数冲突场景下仍有补救空间

## 当前 `POST /api/runs` 返回语义

第一版重点表达：

```text
平台已经接住了这次 run 创建请求，并创建了平台自己的 run 记录。
```

所以当前稳定约定是：

- `status = created`
- `message = Run request accepted.`

不推荐在这一阶段就写成：

- `success`
- `queued`

除非后面业务语义真的已经扩展到对应阶段。

## 相关文档

- [Testing Workflow](testing-workflow.md)
- [Step 7：`POST /api/runs` + SQLite](../steps/step-07-post-runs-and-sqlite.md)
- [Step 8：`GET /api/runs`](../steps/step-08-get-runs-list.md)
- [Step 9：`GET /api/runs/{run_id}`](../steps/step-09-get-run-detail.md)
