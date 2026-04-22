# Step 7：`POST /api/runs` + SQLite 最小闭环

## 这一步的目标

把 `POST /api/runs` 从静态 stub 推进成真正的最小闭环：

- 接口收到请求
- service 生成 `run_id`
- repository 把记录写进 `SQLite`
- 接口返回最小响应

## 当前落地结果

现在这条链路已经具备：

- `POST /api/runs`
- `runs` 表自动初始化
- 最小 run 元数据写入 `SQLite`
- API 测试覆盖创建和落库主链路

## 关键文件

- `platform-api/app/main.py`
- `platform-api/app/services/run_service.py`
- `platform-api/app/repositories/run_repository.py`
- `platform-api/app/schemas/run.py`
- `platform-api/tests/test_runs.py`

## 当前调用链

```text
POST /api/runs
-> router 接请求
-> schema 校验输入
-> service 生成 run_id、状态和时间戳
-> repository 写入 SQLite
-> service 返回 RunCreateResponse
```

## 这一步定下来的设计点

### 为什么要加 repository

因为从这一步开始已经进入“数据持久化”阶段了。

如果继续把 SQL 写在 `router` 或 `service` 里，后面扩列表、详情、状态更新时会越来越乱。

### `core` 是做什么的

当前 `core` 负责全局基础配置，例如：

- `app_name`
- `app_env`
- `runs_db_path`

最短记忆版：

```text
core = 全局基础层，不是 run 业务层。
```

### 当前 `run_id` 规则

当前采用更可读的规则：

- 默认先用 `run-时间戳`
- 如果真的冲突，再补 `-01 / -02`

## 当前验证方式

服务器侧最常用：

```bash
python -m pytest tests/test_health.py tests/test_runs.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl -X POST http://127.0.0.1:8000/api/runs -H "Content-Type: application/json" -d '{"testline":"smoke","robotcase_path":"cases/login.robot"}'
```

## 这一步最适合复盘的点

- `router / service / repository / core` 的职责边界
- 为什么当前只返回 `run_id / status / message`
- 为什么列表和详情接口必须建立在真实落库之上

## 相关专题

- [API 设计与调用链](../guides/api-design-and-flow.md)
- [Testing Workflow](../guides/testing-workflow.md)
