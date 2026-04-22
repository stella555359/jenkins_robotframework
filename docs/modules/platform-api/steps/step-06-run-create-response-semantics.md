# Step 6：`POST /api/runs` 第一版返回语义

## 这一步的目标

这一步不直接扩代码，而是先把 `POST /api/runs` 第一版应该表达什么语义定清楚。

当前结论：

- `run_id`：平台自己的 run 标识
- `status`：先用 `created`
- `message`：先用 `Run request accepted.`

## 为什么这一步很关键

如果这一步不先统一，后面即使代码写出来，也很容易出现：

- 有人写 `created`
- 有人写 `queued`
- 有人写 `success`
- 有人把 `message` 写得很长、很重

所以这一步的重点是先把“最小返回语义”定稳。

## 当前推荐返回值

```json
{
  "run_id": "run-20260421-0001",
  "status": "created",
  "message": "Run request accepted."
}
```

## 当前最值得记住的点

### 为什么推荐 `created`

因为这一阶段最重要的是表达：

```text
平台已经接住了这次 run 创建请求，并创建了平台自己的 run 记录。
```

### 为什么不推荐 `success`

因为 `success` 太容易让人误解成：

- Robot 已经执行成功
- Jenkins 已经跑完成功

但在创建接口刚返回时，这些事情通常都还没发生。

### 为什么当前也先不用 `queued`

`queued` 更适合你已经明确引入了“排队 / 调度”语义时再用。

如果当前只是：

- 接请求
- 生成 `run_id`
- 返回最小结果

那么 `created` 会更稳。

## `message` 的风格

当前建议：

- 简短
- 稳定
- 不夹带太多实现细节

例如：

```text
Run request accepted.
```

## 当前阶段建议怎么复习这一步

你可以只记一句话：

```text
POST /api/runs 第一版先表达“平台已接住请求”，不要误写成“执行已经成功”。
```

## 相关专题

- [API 设计与调用链](../guides/api-design-and-flow.md)
