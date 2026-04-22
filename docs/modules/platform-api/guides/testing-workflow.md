# Platform API Testing Workflow

## 文档定位说明

这份文档的定位是：

```text
项目内长期保留的测试作战手册
```

它不是 Cursor 平台级的 `rule`，也不是系统级 `skill`，而是我们在这个项目里共同沉淀出来的测试 workflow 约定。

你可以这样区分：

- `plan`
  - 表示“这次准备怎么推进”
  - 更偏阶段性方案
- `rule`
  - 表示“以后必须遵守什么”
  - 更偏长期硬约束
- `skill`
  - 表示“某类任务该怎么专业地做”
  - 更偏通用方法论
- `testing-workflow.md`
  - 表示“这个项目里测试相关工作以后默认怎么协作、怎么留档、怎么执行”
  - 更偏项目内长期工作约定

最短记忆版：

```text
plan = 这次怎么做
rule = 必须遵守什么
skill = 这类任务怎么做
testing-workflow = 这个项目里测试怎么协作
```

## 文档目标

这份文档只记录 `platform-api` 当前阶段的测试工作流，不混入具体 step 的实现细节。

你后面如果想快速回看：

- 现在测试分几层
- `fixture` 该怎么理解
- `Allure` 该怎么接
- AI 在测试里能帮什么

优先看这份文档。

## 后续测试交付约定

从当前开始，每个业务 step 的测试部分都会尽量拆成两类文档：

1. `testing-training`
   - 用来沉淀测试设计思路、测试矩阵、风险点和 AI 配合方式

2. `testing-automation`
   - 用来明确记录：
     - 本轮已自动化场景
     - 对应 pytest / fixture / Allure 落地
     - 本轮未自动化场景
     - 为什么这轮还没自动化

也就是说，后面不会只停留在“告诉你该测什么”，而是会继续追踪：

```text
哪些场景已经真的能跑，哪些场景还只是风险提醒。
```

这两个目录后面默认长期保留，不互相替代。

你可以这样使用：

- 想知道“这一轮测试到底自动化了什么、服务器该跑什么”：
  - 优先看 `testing-automation`
- 想知道“这一轮为什么这样测、风险怎么拆、AI 怎么参与测试设计”：
  - 优先看 `testing-training`

最短记忆版：

```text
testing-training = 训练思维
testing-automation = 执行交付
```

## testing-automation 流程图约定

从当前开始，`testing-automation` 下的每一份 step 文档都默认补一张：

- 测试用例执行流程图

这张图回答的重点不是“业务代码内部怎么调用”，而是：

```text
这一轮自动化测试执行时，测试数据、测试场景和最终结果是怎么串起来跑的。
```

默认要求：

- 优先用 `mermaid`
- 优先画“总览图”，不要一开始就把所有细节塞进一张大图
- 如果测试分支较多，采用：
  - 一张简版总览图
  - 下面配每条用例的短步骤清单
- 目标是让人放大后也能一眼看懂，不追求把所有断言都挤进节点里

最短记忆版：

```text
testing-automation 文档默认要有测试流程图；
图负责总览，细节放到图下的分用例说明里。
```

## 后续 canvas 使用约定

从当前开始，这两类测试文档的 canvas 使用规则固定为：

1. `testing-training`
   - 默认同时保留：
     - markdown
     - canvas
   - 原因：测试矩阵、风险点、AI 配合方式这类内容更适合可视化 review

2. `testing-automation`
   - 默认先保留 markdown
   - 当某个 step 的自动化测试内容开始明显变复杂时，再额外补一份 canvas

也就是说：

- `testing-training` 的 canvas 是默认动作
- `testing-automation` 的 canvas 是按复杂度决定的增强动作

最短记忆版：

```text
testing-training 默认 markdown + canvas
testing-automation 默认 markdown，复杂时再补 canvas
```

## 当前阶段的测试主线

在 `platform-api` 当前阶段，最适合先按下面 3 层来理解测试：

1. API 契约层
2. 持久化验证层
3. 系统 / 集成层

最短记忆版：

```text
先测接口会不会说，再测数据库有没有记，最后再测系统是不是整条链路都通。
```

## 第 1 层：API 契约层

这一层最关心：

- 状态码对不对
- 返回 JSON 结构对不对
- 错误语义对不对
- 必填字段和关键字段是否齐全

当前典型工具：

- `fastapi.testclient.TestClient`

当前已经属于这一层的接口：

- `GET /api/health`
- `POST /api/runs`
- `GET /api/runs`
- `GET /api/runs/{run_id}`

## 第 2 层：持久化验证层

这一层最关心：

- 接口调用后，数据库里是否真的产生了预期变化
- 查询接口返回的数据，是否和库里的真实记录一致

当前典型工具：

- `db_connection` fixture

典型场景：

- 创建 run 后，检查 `runs` 表是否真的插入记录
- 详情接口返回的字段，是否和库里的同一条记录一致

## 第 3 层：系统 / 集成层

这一层是后续要逐步引入的能力，重点是：

- FastAPI 和 Jenkins 的调用链
- Jenkins 和 Agent / Robot 的执行链
- 状态回写、产物归档、前端展示是否一致

当前阶段先不做重，但设计和文档会开始为它留位置。

## 当前 fixture 结构

当前公共 fixture 统一放在：

- `platform-api/tests/conftest.py`

现阶段已经有的 fixture：

- `isolated_runs_db`
  - 作用：给测试切一个独立 SQLite 文件，避免互相污染
- `client`
  - 作用：统一创建 `TestClient`
- `db_connection`
  - 作用：直接检查测试数据库里的真实记录
- `create_run_via_api`
  - 作用：统一创建 run 测试数据，避免每条测试重复写 `POST /api/runs`

最短记忆版：

```text
fixture 负责准备环境和公共前置动作，测试函数本身只专注验证目标。
```

## 为什么 `health` 也迁到 API + fixture 风格

虽然 `health` 很简单，但现在也统一改成：

- `TestClient`
- 调真实接口
- Allure 标注

这样做的好处是：

1. 测试风格统一
2. 后面你看测试代码时，不会一部分在测 service，一部分在测 API
3. 更符合测试工程师按接口视角思考的方式

## Allure 的定位

当前只引入最基础的 Allure 能力：

- `allure-pytest`
- `feature / story / title` 标注
- 生成 `allure-results`

要注意：

```text
allure-pytest 负责生成结果文件；
真正把结果渲染成 HTML 报告，还需要 Allure CLI 或 Jenkins 侧的 Allure 能力。
```

当前服务器侧常用命令：

```bash
python -m pytest tests
python -m pytest tests --alluredir=allure-results
allure serve allure-results
```

## Allure HTML 报告什么时候再做

当前阶段先做到：

- `python -m pytest tests --alluredir=allure-results`
- 确认服务器侧能稳定产出 `allure-results`

也就是说，现在先打通的是：

```text
测试结果文件产出链路
```

而不是完整的：

```text
Jenkins 流水线里的 HTML 报告发布链路
```

真正把 Allure HTML 报告做完整，最合适的时机是在后面的 Jenkins 测试流水线阶段。

到那个阶段再一起补：

- Jenkins 侧 Allure 能力（插件或等价发布方式）
- Pipeline 中的 `allure-results` 归档 / 发布步骤
- pytest 与后续 Robot 结果的报告整合方式

最短记忆版：

```text
现在先产出 allure-results；
后面做 Jenkins 测试流水线时，再把 HTML 报告发布补完整。
```

## 当前更推荐的测试节奏

对每个新 step，优先按下面顺序补测试：

1. 先补 API 契约层
2. 再补最少必要的持久化验证层
3. 暂不提前把系统测试做重

这样可以避免在当前阶段过早把测试体系做得太散、太重。

## AI 可以怎么辅助测试

当前阶段最适合的 AI 辅助方式：

- 帮你列接口测试点矩阵
- 帮你发现漏掉的边界值和失败场景
- 帮你生成 pytest 骨架草稿
- 帮你 review 当前测试是不是只测了成功路径

后面接 Jenkins 后，再把 AI 逐步扩展到：

- 状态机风险识别
- 系统测试 checklist
- 故障注入清单

## 相关文档

- [API 设计与调用链](api-design-and-flow.md)
- [Step 9 测试自动化](../testing-automation/step-09-test-automation.md)
- [Step 9 测试设计训练](../testing-training/step-09-test-training.md)
- [Step 6：`POST /api/runs` 返回语义](../steps/step-06-run-create-response-semantics.md)
- [Step 7：`POST /api/runs` + SQLite](../steps/step-07-post-runs-and-sqlite.md)
- [Step 8：`GET /api/runs`](../steps/step-08-get-runs-list.md)
- [Step 9：`GET /api/runs/{run_id}`](../steps/step-09-get-run-detail.md)
