# FastAPI 入门说明
## 面向 `reporting-portal` 的通俗讲解

## 1. 先一句话理解

在你现在这个项目里，`reporting-portal` 这层 `FastAPI`，可以把它理解成：

- 前面接 `automation-portal` React 页面
- 后面接 Jenkins、数据库、KPI 结果、artifact
- 专门负责“收请求、做判断、调后端、回结果”的中间层

如果用很通俗的话说：

- `automation-portal` 是前台页面
- Jenkins 是执行车间
- `reporting-portal` 是前台和车间之间的调度台

它不是直接跑 Robot 的地方，也不是最终给用户看的页面，而是“平台后端”。

---

## 2. 为什么这里要用 FastAPI

你这个项目后面要做的事情，本质上很适合 API 后端：

1. 接收前端发来的请求
2. 校验参数
3. 记录一次 run
4. 调 Jenkins 触发 job
5. 回传 run 状态
6. 返回给前端 JSON 数据

FastAPI 特别适合这类场景，原因很简单：

- 写接口很快
- 参数校验很方便
- JSON API 天然合适
- 和 Python 生态贴得近
- 以后接 Jenkins、KPI 后处理、SQLite/PostgreSQL 都方便

所以你这里用 FastAPI，不是为了“追新框架”，而是因为它正好适合做这种平台后端。

---

## 3. FastAPI 本质上在做什么

FastAPI 的核心工作流程，其实可以很简单地理解成下面这条链路：

```text
浏览器 / 前端
    ->
HTTP 请求
    ->
FastAPI 路由函数
    ->
业务逻辑
    ->
数据库 / Jenkins / 文件 / 外部服务
    ->
返回 JSON
    ->
前端页面展示
```

也就是说，FastAPI 本身不神秘。

它主要帮你做三件事：

1. 把 URL 和 Python 函数对应起来
2. 帮你校验输入和输出
3. 帮你把结果转成 HTTP 响应

---

## 4. 在这个项目里，`reporting-portal` 的职责是什么

在你现在的设计里，`reporting-portal` 不再只是“结果展示服务”，而是统一后端。

它后面至少要承担这些职责：

- 提供 `/api/health`
- 提供 `run` 的创建与查询接口
- 封装 Jenkins 的调用
- 保存 run 元数据
- 保存 build 状态
- 保存 artifact 信息
- 保存 KPI 结果链接和摘要

所以它更像：

- 平台后端
- 任务记录中心
- 结果聚合层

而不是简单的“一个健康检查接口”。

---

## 5. 在这个项目里，数据库准备怎么用

在你当前这套轻量化方案里，`reporting-portal` 第一轮默认会接一个数据库，而且建议直接用：

- `SQLite`

这里要特别注意：

- FastAPI 不是数据库
- 但 `reporting-portal` 需要数据库来保存平台运行记录

你可以先把 SQLite 理解成：

- 一个很轻量的本地数据库文件
- 不需要单独装数据库服务
- 很适合你当前练手阶段

在这个项目里，SQLite 主要拿来存：

- `run_id`
- job 名称
- branch
- testline
- case 名
- 当前状态
- Jenkins build number
- 开始时间 / 结束时间
- artifact 链接
- 后续 KPI 结果链接和摘要

也就是说，它存的是“平台元数据”，不是大文件本体。

例如：

- 数据库存 run 记录、状态、路径、链接
- Jenkins / 文件系统存 `output.xml`、`log.html`、KPI `.xlsx`、HTML 报告

这就是最适合你当前阶段的做法。

## 6. 你可以把它想成一个“接线员”

假设用户在 React 页面点了“运行 case”。

这时真正发生的事不是：

- React 直接去调 Jenkins

而是：

1. React 把参数发给 `reporting-portal`
2. `reporting-portal` 检查参数
3. `reporting-portal` 先生成一条 `run_id`
4. `reporting-portal` 调 Jenkins 触发 job
5. Jenkins 返回 queue / build 信息
6. `reporting-portal` 把这些信息保存下来
7. React 再去查 `run_id` 对应的状态

所以 `reporting-portal` 的作用就是：

- 不让前端直接碰 Jenkins
- 把业务概念和 Jenkins 技术概念隔开

这也是为什么前面一直强调：

`React -> FastAPI -> Jenkins`

而不是：

`React -> Jenkins`

---

## 7. 一个最小 FastAPI 服务通常长什么样

后面你真正写起来的时候，一般会有这几层：

```text
app/
├── main.py
├── api/
│   └── v1/
│       └── router.py
├── schemas/
├── services/
├── repositories/
├── models/
└── core/
```

你可以这样理解：

### `main.py`

项目入口。

作用：

- 创建 `FastAPI()` 应用对象
- 注册路由
- 配置基础中间件

可以理解成“服务总开关”。

### `api/v1/router.py`

路由层。

作用：

- 定义有哪些接口
- 比如 `GET /api/health`
- 比如 `POST /api/runs`

可以理解成“前台窗口”。

### `schemas/`

数据结构定义层。

作用：

- 定义请求体长什么样
- 定义返回体长什么样

比如：

- 创建 run 时要哪些字段
- 返回 run 详情时有哪些字段

这是 FastAPI 里非常重要的一层，因为它能帮你自动做参数校验。

### `services/`

业务逻辑层。

作用：

- 真正处理“创建 run”
- 真正处理“触发 Jenkins”
- 真正处理“更新状态”

可以理解成“真正干活的人”。

### `repositories/`

数据访问层。

作用：

- 专门读写数据库
- 让数据库操作不要散落在路由里

可以理解成“专门负责查表和写表的人”。

### `models/`

数据库模型层。

作用：

- 定义数据库里有哪些表和字段

### `core/`

配置层。

作用：

- 管环境变量
- 管应用名、端口、数据库连接等配置

---

## 8. 你后面写代码时，最重要的原则

最容易犯的一个错误是：

- 把所有代码都写进 `router.py`

这样短期看很快，长期会很乱。

更推荐的做法是：

- `router.py` 只收请求和回响应
- `service` 处理业务逻辑
- `repository` 处理数据库
- `schema` 处理数据结构

也就是：

```text
route 不直接写复杂逻辑
service 不直接拼 HTTP 响应
repository 不关心前端页面
```

这样后面加 Jenkins、KPI、artifact 时才不会很快失控。

---

## 9. 先用一个最小例子理解

比如后面你要做：

- `POST /api/runs`

这个接口的真实分工应该是：

### 路由层做什么

- 接收前端传来的 JSON
- 调用 `run_service.create_run()`
- 返回 JSON

### schema 层做什么

- 定义创建 run 的请求结构
- 定义返回 run 的响应结构

### service 层做什么

- 生成 `run_id`
- 组装 run 数据
- 调 Jenkins
- 更新状态

### repository 层做什么

- 保存到数据库
- 按 `run_id` 查询

---

## 10. FastAPI 和 Flask 最大的体感区别

你之前做过 Flask 项目，所以这里可以直接对比理解。

### Flask 更像

- 你自己拼很多东西
- 灵活
- 轻
- 但结构容易慢慢发散

### FastAPI 更像

- 默认更强调类型和数据结构
- 路由、请求体、响应体更清晰
- 更适合写规范的 JSON API

所以如果你现在这个项目重点是：

- API 清晰
- 参数规范
- 前后端分离
- 后面接口会越来越多

那么 FastAPI 会比 Flask 更顺手。

---

## 11. 在这个项目里，FastAPI 不负责什么

这点也很重要。

`reporting-portal` 虽然是平台后端，但它不应该负责：

- 直接做 React 页面
- 直接承担所有长时间任务执行
- 直接代替 Jenkins 跑 Robot
- 直接把所有 KPI 计算都塞进 Web 请求里

更合理的分工是：

- React 负责展示和触发
- FastAPI 负责接入、记录、聚合
- Jenkins 负责执行和编排

所以你后面看到要触发 `kpi-generator` 或 `kpi-anomaly-detector` 时，也不要第一反应把它塞进 FastAPI 里直接跑。

FastAPI 更适合：

- 接收请求
- 保存状态
- 调 Jenkins
- 查询结果

---

## 12. 你后面第一轮真正要写什么

你现在不需要一上来把整个 `reporting-portal` 全写完。

第一轮只需要把最小闭环搭起来：

### 第一轮最小接口

- `GET /api/health`
- `POST /api/runs`
- `GET /api/runs`
- `GET /api/runs/{run_id}`

### 第一轮最小数据

- `run_id`
- `job_name`
- `branch`
- `testline`
- `case_name`
- `status`
- `trigger_user`
- `start_time`
- `end_time`

### 第一轮最小目标

做到这三件事就够：

1. 前端能创建一次 run
2. 后端能保存 run
3. 后端能把 run 列表和详情返回出来

先不要一开始就做：

- KPI 全流程
- 异常检测
- 复杂权限
- 大量历史统计

---

## 13. 一个更贴近你项目的类比

如果把整个系统想成一家工厂：

- `automation-portal` 是接待台
- `reporting-portal` 是调度室
- Jenkins 是生产线总调度
- Agent 是工位
- Robot Framework 是具体工序
- KPI 模块是质检和分析

在这个类比里，`reporting-portal` 的核心价值就是：

- 让接待台不用直接操控生产设备
- 让生产线执行情况有统一记录
- 让后续质检和分析结果能统一回收

这就是它在整个项目里的意义。

---

## 14. 你现在最该记住的三句话

1. `reporting-portal` 不是页面，它是平台后端。
2. FastAPI 最擅长做“清晰的 JSON API + 参数校验 + 平台中间层”。
3. 你第一轮先把 run 接口做出来，比先做复杂页面更重要。

---

## 15. 当前项目里的实际提醒

你当前仓库里的 `reporting-portal` 还只是很薄的占位状态，说明：

- 目录已经预留了
- `.env.example` 已存在
- 但真正的 `app/main.py`、`router.py`、`service`、`schema` 这些核心代码，还需要你接下来一步步补起来

这正好适合你从最小 API 开始练手。

---

## 16. 下一步建议

在真正动手写代码前，最合适的下一步是：

1. 先把 `reporting-portal` 的最小目录结构重新补齐
2. 先写 `GET /api/health`
3. 再写 `POST /api/runs`
4. 再写 `GET /api/runs`
5. 最后再接前端页面

这样顺序最稳，也最容易理解整套架构。
