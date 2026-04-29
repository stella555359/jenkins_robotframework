# jenkins_robotframework

## 项目定位

这个仓库当前承载的是一条逐步落地中的自动化测试平台主线，核心目标是：

- 用 `platform-api` 承担平台后端能力
- 后续接 Jenkins / Agent / Robot / KPI
- 同时把 AI 自动化测试 workflow 逐步做进平台搭建过程本身

## 顶层目录怎么理解

### `docs/`

文档总入口。

如果你现在不知道该看哪份文档，先看：

- `docs/README.md`

这里现在已经统一整理为：

- `docs/overview/`
  - 项目级路线和跨模块文档
- `docs/modules/`
  - 按模块拆开的主文档
- `docs/archive/`
  - 历史 / 参考文档

### `platform-api/`

当前正在重点推进的 FastAPI 后端。

这里放：

- `app/`
- `tests/`
- `requirements.txt`
- `pytest.ini`

如果你现在正在做接口、测试、fixture、Allure 相关工作，通常优先进入这里。

### `jenkins-integration/`

Jenkins 公共集成层骨架。

这里放：

- `jcasc/`
- `jobs/`
- `pipelines/`
- `scripts/`

如果你现在正在收口 Jenkins trigger、Pipeline、workspace bootstrap、checkout `robotws / testline_configuration`、callback 这些公共逻辑，优先进入这里。

### `automation-portal/`

后续的前端门户层。

当前还不是主推进重点，但后面会接上：

- 触发页面
- run 列表 / 详情页
- KPI 展示

### `issue/`

历史问题记录、专项分析、排障资料。

它更像项目内的工作备忘和问题归档，不是当前主线实现入口。

### `.cursor/`

项目级 Cursor 规则和辅助配置，例如：

- `rules/`
- `skills/`

这部分更多是 AI 协作辅助，不是业务源码主入口。

## 当前推荐的进入路径

### 如果你想继续推进业务主线

1. 先看 `docs/README.md`
2. 如果想看项目总路线，进 `docs/overview/roadmap.md`
3. 如果想看 Jenkins 公共集成层，进 `docs/modules/jenkins-integration/`
4. 如果想看当前模块，进 `docs/modules/platform-api/`
5. 然后去对应模块目录看代码和测试
6. 如果当前是在推进 GNB KPI 新主线，再补看 `docs/modules/platform-api/guides/gnb-kpi-regression-architecture.md`

### 如果你想回看测试 workflow

1. 先看 `docs/modules/platform-api/guides/testing-workflow.md`
2. 再看：
   - `docs/modules/platform-api/testing-training/`
   - `docs/modules/platform-api/testing-automation/`

## 当前命名理解规则

你后面可以先按这个规则快速判断文件用途：

- `docs/overview/` = 项目总览
- `docs/modules/<module>/guides/` = 模块稳定专题
- `docs/modules/<module>/steps/` = 模块单步实现记录
- `docs/modules/<module>/testing-training/` = 模块测试思维训练
- `docs/modules/<module>/testing-automation/` = 模块测试自动化交付

最短记忆版：

```text
docs 管入口和知识
overview 管项目总览
modules 管模块文档
jenkins-integration 管公共 Jenkins 层
platform-api 管当前主代码
automation-portal 管后续前端
issue 管历史问题归档
```
