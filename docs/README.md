# Docs Start Here

## 文档定位

这份文档是整个 `docs/` 目录的总导航。

从这一轮开始，`docs/` 不再默认围绕单一 `platform-api` 模块组织，而是统一升级为三层结构：

```text
docs/
  README.md
  overview/
  modules/
  archive/
```

最短理解版：

```text
overview = 项目总览
modules = 按模块拆开的主文档
archive = 历史 / 参考材料
```

## 当前推荐阅读顺序

### 1. 想先看整个项目方向

- [Overview Docs](overview/README.md)
- [项目路线图](overview/roadmap.md)
- [GNB KPI Regression Architecture](overview/gnb-kpi-regression-architecture.md)
- [GNB KPI System Runtime](overview/gnb-kpi-system-runtime.md)

这部分负责回答：

- 整个项目最终要做成什么
- 模块之间怎么串起来
- 系统运行时怎么协作
- 当前主线应该往哪里推进

### 2. 想进入某个具体模块

当前已落地的模块入口：

- [Platform API Docs](modules/platform-api/README.md)
- [Test Workflow Runner Docs](modules/test-workflow-runner/README.md)
- [Automation Portal Docs](modules/automation-portal/README.md)

进入模块后，再按模块自己的 `README.md -> index.md -> guides / steps / testing` 顺序看。

### 3. 想回看历史资料

- [Archive Docs](archive/README.md)

这部分只放历史版本、参考材料和过渡稿，不作为当前默认主入口。

## 当前 docs 目录怎么理解

### `overview/`

放项目级文档，例如：

- 路线图
- 跨模块架构
- 系统级 runtime
- 端到端主线

当前入口：

- [Overview Docs](overview/README.md)

### `modules/`

放模块级文档。

每个模块后续统一采用同一套骨架：

```text
docs/modules/<module>/
  README.md
  index.md
  guides/
  steps/
  testing-training/
  testing-automation/
```

当前已落地模块：

- `platform-api`
- `test-workflow-runner`
- `automation-portal`

当前入口：

- [Platform API Docs](modules/platform-api/README.md)
- [Platform API 学习总索引](modules/platform-api/index.md)
- [Test Workflow Runner Docs](modules/test-workflow-runner/README.md)
- [Automation Portal Docs](modules/automation-portal/README.md)

### `archive/`

放不再作为当前主入口、但仍值得保留的文档。

当前入口：

- [Archive Docs](archive/README.md)

## 当前 `platform-api` 模块包含什么

`platform-api` 下面现在已经按模块内部分层整理为：

- `guides/`
  - 稳定专题知识
- `steps/`
  - 单步实现记录
- `testing-training/`
  - 测试设计训练材料
- `testing-automation/`
  - 测试自动化交付记录

当前优先入口：

- [模块 README](modules/platform-api/README.md)
- [模块总索引](modules/platform-api/index.md)
- [Testing Workflow](modules/platform-api/guides/testing-workflow.md)
- [API 设计与调用链](modules/platform-api/guides/api-design-and-flow.md)

## 后续新模块怎么接入

后面如果新增：

- `automation-portal`
- `test-workflow-runner`

默认都放到：

- `docs/modules/<module>/`

并沿用和 `platform-api` 一样的骨架，不再新建全局型的 `testing-training/` 或 `testing-automation/` 目录。

## 历史 / 参考类文档

这类文档现在统一放到：

- `docs/archive/`

当前已归档的文件包括：

- `archive/new_jekins_lightweight_fixed.md`
- `archive/original_jenkins_robotframework.md`
- `archive/5g_jenkins_robotframework.md`
- `archive/FASTAPI_introduction.md`
- `archive/jenkins_kpi_platform_implementation_guide.md`

这些文件当前建议理解为：

- 历史版本
- 参考材料
- 过渡文档

## `docs` 和 `issue` 怎么分工

从项目管理角度，`docs/` 和 `issue/` 默认不要混成一类目录，而是固定这样分工：

### 放进 `docs/` 的内容

- 当前有效的正式文档
- 面向长期复用的知识沉淀
- 模块说明、step 记录、testing workflow、架构说明
- 适合后面反复回看的内容

### 放进 `issue/` 的内容

- 单次问题处理过程
- 排障记录
- 临时分析
- 取证材料
- 面向“这次发生了什么、怎么排、结论是什么”的记录

也就是说：

```text
docs = 正式、长期、可复用
issue = 过程、问题、排障、记录
```

如果某份 `issue` 内容后面已经沉淀成稳定知识，更推荐的做法是：

1. 把整理后的正式版本补进 `docs/`
2. 保留原始 `issue` 记录
3. 必要时在 `issue` 里补一句“正式版本见 docs/...”

## 后续推进时先看哪个文档

从当前开始，后续推进顺序固定按下面两层判断：

### 第一层：先看项目主线

优先看：

- `docs/overview/roadmap.md`

它负责决定：

- 当前整个项目先推进哪个模块
- 模块之间的大顺序怎么排
- 当前主线应该往哪个方向继续

### 第二层：再看模块内下一步

确定模块之后，再看：

- `docs/modules/<module>/index.md`

它负责决定：

- 这个模块当前做到哪一步
- 下一步具体做哪个 step
- 当前应该优先回看哪些 guides / steps / testing 文档

最短记忆版：

```text
roadmap 决定先做哪个模块
module index 决定这个模块下一步做哪个 step
guides 负责解释方法和设计，不负责排推进顺序
```

如果后面 Cursor 重启，需要最快恢复上下文，默认按下面路径：

1. 先看 `docs/README.md`
2. 再看 `docs/overview/roadmap.md`
3. 再看当前模块 `docs/modules/<module>/index.md`

## 这轮整理的结果

这一轮完成后，后面恢复上下文时可以按下面路径走：

1. 先看 `docs/README.md`
2. 想看项目大图景，进 `docs/overview/`
3. 想看具体模块，进 `docs/modules/<module>/`
4. 想看历史资料，再进 `docs/archive/`
