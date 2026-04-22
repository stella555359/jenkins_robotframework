# Step 8：`GET /api/runs` 列表接口

## 这一步的目标

把已经写进 `SQLite` 的 run 记录查出来，并以列表形式返回。

这一步补上的不是新写入能力，而是最小读取能力。

## 当前落地结果

现在已经具备：

- `GET /api/runs`
- 从 `runs` 表真实查询数据
- 按 `created_at` 倒序返回
- 响应结构先用 `items` 包一层

## 当前返回结构

```json
{
  "items": [
    {
      "run_id": "run-20260422104958123",
      "testline": "smoke",
      "robotcase_path": "cases/login.robot",
      "status": "created",
      "message": "Run request accepted.",
      "created_at": "2026-04-22T10:49:58.123+08:00",
      "updated_at": "2026-04-22T10:49:58.123+08:00"
    }
  ]
}
```

## 当前调用链

```text
GET /api/runs
-> router 接请求
-> service 调 repository 查列表
-> repository 从 SQLite 的 runs 表读取数据
-> service 组装 RunListResponse(items=[...])
```

## 这一步定下来的设计点

### 为什么一定要查数据库

因为当前 run 列表的真实数据来源就是 `runs` 表。

最短记忆版：

```text
GET /api/runs 不是返回假数据，而是把之前写进去的 run 再查出来。
```

### 为什么先用 `items` 包一层

因为后面如果要扩：

- `total`
- 分页信息
- 筛选条件回显

对象结构会比裸数组更稳。

## 当前测试重点

- 创建两条 run 后再查列表
- 最新创建的记录在前面
- 列表字段是否和数据库一致

## 当前最适合复盘的点

- 列表接口和创建接口的职责差异
- 为什么 `items` 包一层更利于扩展
- 为什么“接口能读出来”是和“接口能写进去”不同的闭环

## 相关专题

- [API 设计与调用链](../guides/api-design-and-flow.md)
- [Testing Workflow](../guides/testing-workflow.md)
