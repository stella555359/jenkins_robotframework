# Step 9：`GET /api/runs/{run_id}` 详情接口

## 这一步的目标

把“按 `run_id` 精确查询单条 run 记录”这条链路打通。

当前需要明确两件事：

- 已知 `run_id` 时，能查到这条 run 的详情
- 查不到时，要明确返回 `404`

## 当前落地结果

现在已经具备：

- `GET /api/runs/{run_id}`
- 按 `run_id` 从 `runs` 表查单条记录
- 查不到返回 `404`
- 测试覆盖命中路径和未命中路径

## 当前调用链

```text
GET /api/runs/{run_id}
-> router 接 path 参数
-> service 决定“查到/查不到”的业务语义
-> repository 从 SQLite 按 run_id 查询
-> service 返回 RunDetailResponse 或抛 404
```

## 这一步定下来的设计点

### 为什么已经有列表了，还要有详情

因为列表接口解决：

- 有哪些 run

详情接口解决：

- 这一条 run 到底是什么

最短记忆版：

```text
列表接口解决“有哪些”，详情接口解决“这一条是什么”。
```

### 为什么查不到要返回 `404`

因为这里的语义是“资源不存在”，不是“字段为空”。

不推荐：

- `200 + {}`

推荐：

- `404`
- `{"detail": "Run not found."}`

## 这一步带出的测试工程强化

从这一轮开始，测试工程顺手往前推进了两步：

1. fixture 收敛
   - `tests/conftest.py`
   - `isolated_runs_db`
   - `client`
   - `db_connection`
   - `create_run_via_api`

2. Allure 基础接入
   - `allure-pytest`
   - `feature / story / title`

## 当前测试重点

- 命中路径：已有 `run_id` 时能否正确返回详情
- 未命中路径：不存在的 `run_id` 是否稳定返回 `404`
- 一致性：列表能看到的 run，详情能否按同一 `run_id` 查到

## 服务器侧常用命令

```bash
python -m pytest tests/test_health.py tests/test_runs.py
python -m pytest tests/test_health.py tests/test_runs.py --alluredir=allure-results
allure serve allure-results
```

## 当前最适合复盘的点

- 详情接口为什么不能用假数据顶替
- 为什么 `404` 比 `200 + {}` 更利于接口语义和测试判断
- fixture 和 Allure 在这个阶段分别解决了什么工程问题

## 相关专题

- [Testing Workflow](../guides/testing-workflow.md)
- [API 设计与调用链](../guides/api-design-and-flow.md)
- [Step 9 测试设计训练](../testing-training/step-09-test-training.md)
- [Step 9 测试自动化](../testing-automation/step-09-test-automation.md)
