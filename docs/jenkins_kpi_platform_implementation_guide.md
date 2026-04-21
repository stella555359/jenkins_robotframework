# Jenkins KPI Platform 实施指南
## 本地 IDE 开发 + GitHub 同步 + Debian 服务器部署

**文档版本**：v2.0  
**更新日期**：2026-04-16  
**适用环境**：Windows 本地开发机 + Debian 13 / Ubuntu 22.04+ 服务器  
**GitHub 仓库**：https://github.com/stella555359/jenkins_robotframework

**当前环境参数**：

- 本地 Windows 用户：`stlin`
- 本地仓库路径：`C:\TA\jenkins_robotframework`
- Master 服务器：`10.71.210.104`
- Agent 服务器：`10.57.159.149`
- Debian SSH 用户：`ute`

---

## 目录

- [实施原则](#实施原则)
- [故障现象快速入口](#故障现象快速入口)
- [总体架构](#总体架构)
- [第一步：前置准备](#第一步前置准备)
- [第二步：GitHub 仓库与本地开发模式](#第二步github-仓库与本地开发模式)
- [第三步：服务器基础环境准备](#第三步服务器基础环境准备)
- [第四步：Jenkins Master 部署](#第四步jenkins-master-部署)
- [第五步：三块代码的开发与部署方式](#第五步三块代码的开发与部署方式)
- [第六步：Jenkins Agent 配置](#第六步jenkins-agent-配置)
- [第七步：Pipeline 与代码同步流程](#第七步pipeline-与代码同步流程)
- [第八步：验证与日常运维](#第八步验证与日常运维)
- [故障排查](#故障排查)
- [Jenkins 排障清单](#jenkins-troubleshooting-checklist)
- [Nginx 排障清单](#nginx-troubleshooting-checklist)
- [Portal 排障清单](#portal-troubleshooting-checklist)

---

<a id="quick-troubleshooting-entry"></a>

## 故障现象快速入口

如果你现在不是在按步骤实施，而是在现场排障，先不要急着重启服务。先按下面这张表判断“第一套该跑的命令清单”即可。

| 现象 | 先跑哪套命令 |
|---|---|
| 浏览器连不上 / 超时 / `Failed to connect` | [Nginx 排障清单](#nginx-troubleshooting-checklist) |
| `https://10.71.210.104/jenkins/` 返回 `404` | 先看 [Nginx 排障清单](#nginx-troubleshooting-checklist)，再看 [Jenkins 排障清单](#jenkins-troubleshooting-checklist) |
| Jenkins 页面返回 `502` | [Jenkins 排障清单](#jenkins-troubleshooting-checklist) |
| `/api/` 或 `/kpi/` 返回 `502` | [Portal 排障清单](#portal-troubleshooting-checklist) |
| Jenkins 登录跳转异常 / 资源 404 / URL 很怪 | [Jenkins 排障清单](#jenkins-troubleshooting-checklist) |
| `/api/health` 不通 | [Portal 排障清单](#portal-troubleshooting-checklist) |
| `/kpi/health` 不通 | [Portal 排障清单](#portal-troubleshooting-checklist) |
| Jenkins 本机能通、外部 HTTPS 不通 | [Nginx 排障清单](#nginx-troubleshooting-checklist) |
| Portal 本机健康检查能通、外部路径不通 | [Nginx 排障清单](#nginx-troubleshooting-checklist) |

最短记忆规则：

- 连不上：先查 Nginx
- `502`：先查后端服务
- Jenkins 跳转异常：先查 Jenkins
- Portal 健康检查异常：先查 Portal

---

## 实施原则

这份文档采用以下固定原则，后续所有步骤都以此为准：

1. **`jenkins-kpi-platform`、`kpi-portal`、`platform-api` 这三块代码不在 Debian 服务器上直接编写。**
2. **所有代码统一在本地 IDE 中开发、调试、提交。**
3. **唯一的版本管理与同步入口是 GitHub 仓库**：`https://github.com/stella555359/jenkins_robotframework`
4. **服务器只负责部署和运行**，即执行 `git pull`、安装依赖、迁移配置、重启服务。
5. **以后任何代码修改都通过 Git 提交记录版本**，而不是直接在服务器上手改文件。

这意味着：

- 本地电脑是开发环境
- GitHub 是代码真源（source of truth）
- Debian 服务器是运行环境

---

## 总体架构

推荐把三块代码统一维护在同一个 GitHub 仓库中，采用 monorepo 方式管理。

### 推荐目录结构

```text
jenkins_robotframework/
├── jenkins-kpi-platform/
│   ├── jcasc/
│   ├── jobs/
│   ├── pipelines/
│   ├── scripts/
│   └── README.md
├── kpi-portal/
│   ├── app/
│   ├── requirements.txt
│   └── README.md
├── platform-api/
│   ├── app/
│   ├── requirements.txt
│   └── README.md
├── deploy/
│   ├── systemd/
│   ├── nginx/
│   ├── env/
│   └── scripts/
└── docs/
```

### 三块代码的职责

- **jenkins-kpi-platform**：Jenkins 配置、JCasC、Pipeline、部署脚本、自动化编排逻辑
- **kpi-portal**：KPI 分析和报告生成入口服务
- **platform-api**：测试结果查询、汇总、展示 API 或页面服务

**补充说明**：

- 当前两个 FastAPI 服务的实际入口文件都是 `app/main.py`
- 也就是说，启动方式是 `uvicorn app.main:app`
- 当前仓库没有额外创建根目录 `main.py`，这是刻意简化后的结构，不影响运行
- 如果后续你想增加一个根目录 `main.py` 作为启动包装器，也可以再补，但不是必须项

### 推荐发布路径

服务器上统一克隆仓库到：

```bash
/opt/jenkins_robotframework
```

三个服务从该仓库的子目录运行：

- `/opt/jenkins_robotframework/jenkins-kpi-platform`
- `/opt/jenkins_robotframework/kpi-portal`
- `/opt/jenkins_robotframework/platform-api`

这样做的好处是：

- 代码版本统一
- 发布动作统一
- 回滚方便
- 不会出现服务器文件和 Git 仓库脱节

---

## 第一步：前置准备

### 1.1 资源清单

**硬件资源**：

- [ ] Master 服务器：10.71.210.104
- [ ] Agent 服务器：10.57.159.149
- [ ] 两台服务器网络互通

**账号与权限**：

- [ ] GitHub 账号可正常使用
- [ ] GitHub 仓库可访问：`https://github.com/stella555359/jenkins_robotframework`
- [ ] 服务器具备 sudo 权限
- [ ] GitLab 可读取 `robotws`、`testline_configuration` 等现有仓库

**本地开发环境**：

- [ ] Windows 本地已安装 Git
- [ ] 本地 IDE 可正常使用（VS Code / PyCharm 均可）
- [ ] 本地已安装 Python
- [ ] 本地可通过 SSH 连接 Debian 服务器

### 1.2 开发与部署边界

从现在开始，职责边界固定如下：

**本地 IDE 负责**：

- 新功能开发
- Bug 修复
- 单元测试
- 配置文件维护
- 提交 Git 版本

**GitHub 仓库负责**：

- 保存代码主线
- 管理历史版本
- 作为服务器同步源

**Debian 服务器负责**：

- 拉取最新代码
- 安装依赖
- 配置 systemd
- 启动/重启服务
- 供 Jenkins 和业务服务运行

### 1.3 服务器动作执行总原则

从这一节开始，整篇文档中的服务器命令块统一按下面三段式阅读：

1. 动作标签
2. 命令块
3. 解释说明

固定标签格式如下：

- `服务器动作标签：允许做 / 运行目录 / mkdir`
- `服务器动作标签：允许做 / 运行配置文件 / tee`
- `服务器动作标签：谨慎做 / 运行配置文件 / systemctl edit`
- `服务器动作标签：禁止做 / 业务源码文件 / vim nano touch cat >`

### 1.3.1 服务器动作分类总表

| 动作/命令 | 默认分类 | 允许场景 | 禁止或不推荐场景 |
|---|---|---|---|
| `mkdir` | 谨慎做 | 创建运行目录、日志目录、部署目录 | 用来创建 `app/`、`tests/`、`requirements.txt` 所在源码结构 |
| `tee` | 谨慎做 | 写入 `systemd`、`sudoers`、APT 源、运行配置 | 用来直接写业务源码文件 |
| `cp` | 谨慎做 | 把仓库内部署配置复制到 `/etc/...` | 手工复制并长期维护业务源码副本 |
| `git pull` | 允许做 | 服务器同步 GitHub 最新代码 | 服务器工作区有脏改动却强行覆盖时 |
| `pip install` | 允许做 | 安装或更新服务器运行依赖 | 把它当作替代源码提交的手段 |
| `systemctl` | 谨慎做 | `status`、`enable`、`restart` 已知服务 | 在错误时机重启 Jenkins 本体或盲目改服务配置 |
| `vim` / `nano` / `touch` / `cat >` | 禁止做 | 仅限极少数临时运维排障且不涉及业务源码 | 直接创建或长期维护业务源码文件 |

### 1.3.2 一眼判断规则

- 和操作系统、服务启动、代理转发、运行环境有关的，通常属于允许做或谨慎做
- 和业务逻辑、接口实现、依赖清单、测试代码有关的，默认禁止在服务器上直接创建或维护
- 如果一个动作会改变 `/etc/...`、service、代理配置、Jenkins 配置，通常归类为 `运行配置文件`
- 如果一个动作会改变 `app/*.py`、`requirements.txt`、`tests/*`，通常归类为 `业务源码文件`

---

## 第二步：GitHub 仓库与本地开发模式

这一章是整个方案的核心。以后 `jenkins-kpi-platform`、`kpi-portal`、`platform-api` 的任何改动都走这里。

### 2.1 本地克隆 GitHub 仓库

在本地 Windows 机器上执行：

```powershell
cd C:\TA
git clone https://github.com/stella555359/jenkins_robotframework.git
cd C:\TA\jenkins_robotframework
```

如果你已经像当前环境一样先在本地创建好了目录结构，但还没有初始化 Git 仓库，则按下面这组命令做第一次提交：

```powershell
cd C:\TA\jenkins_robotframework
git init
git branch -M main
git add .
git status
git commit -m "chore: initialize jenkins robotframework project scaffold"
git remote add origin https://github.com/stella555359/jenkins_robotframework.git
git push -u origin main
```

如果 `git remote add origin` 报错提示远程已存在，则改用：

```powershell
git remote set-url origin https://github.com/stella555359/jenkins_robotframework.git
git push -u origin main
```

如果远端仓库已经有初始化提交，第一次 push 被拒绝，则执行：

```powershell
git fetch origin
git pull origin main --allow-unrelated-histories
git push -u origin main
```

### 2.2 本地开发分支建议

推荐最少使用以下分支策略：

- `main`：稳定发布分支
- `dev`：日常集成分支
- `feature/*`：功能开发分支
- `fix/*`：缺陷修复分支

建议按下面的职责分工来使用，避免分支越来越乱：

- `main` 只放已经确认可发布的版本，不直接在这个分支上做日常开发
- `dev` 作为日常集成分支，多个功能完成自测后先合到这里统一联调
- `feature/*` 一次只承载一个明确功能或一个小主题，不要在同一个 feature 分支里混做多个无关需求
- `fix/*` 用于明确缺陷修复，优先保持小而快，避免把新功能顺手混进去

### 2.2.1 实际项目中的推荐分工

可以按下面这套方式理解：

1. 平时开发站在 `feature/*` 或 `fix/*`
2. 日常联调和阶段集成站在 `dev`
3. 需要正式发布时，再把确认稳定的内容进入 `main`

更具体一点：

- 新功能开发：从 `dev` 切出 `feature/xxx`
- 缺陷修复：普通缺陷从 `dev` 切出 `fix/xxx`；线上紧急缺陷如果必须立即发版，可从 `main` 切出 `fix/xxx`，修完后再回补到 `dev`
- 日常多人并行：每个人只维护自己的短生命周期分支，不共用同一个 feature 分支
- 阶段验收：先看 `dev` 是否稳定，再决定是否合入 `main`

### 2.2.2 保持分支不凌乱的规则

建议固定执行以下规则：

1. 一个分支只做一件事
2. 分支名字直接反映主题，例如 `feature/reporting-api`、`fix/git-proxy-doc`
3. 小步提交，不要把很多天的大杂烩一次性塞进一个 commit
4. 功能完成并合并后，及时删除对应的 `feature/*` 或 `fix/*` 分支
5. 不要长期让 `feature/*` 分支存活太久，时间越长，后面解决冲突越痛苦
6. 不要把服务器上的临时修改、调试打印、无关格式化一起带进功能分支
7. 合并前先同步目标分支最新代码，确保不是拿过期分支去提合并

### 2.2.3 对当前项目最实用的简化流程

如果你现在项目规模还不大，最实用的落地方式其实是：

1. `main`：只保留稳定可发布版本
2. `dev`：你日常准备合并的主工作面
3. `feature/*`：每个功能一个分支，做完就合回 `dev`
4. `fix/*`：每个问题一个分支，修完就合回 `dev` 或 `main`

推荐日常顺序：

```powershell
git checkout dev
git pull origin dev
git checkout -b feature/platform-api
```

功能完成后：

```powershell
git checkout dev
git pull origin dev
git merge feature/platform-api
git push origin dev
```

等 `dev` 验证稳定后，再进入 `main`：

```powershell
git checkout main
git pull origin main
git merge dev
git push origin main
```

如果后续团队人数变多、发布频率变高，再考虑加更严格的合并审批、标签发布和 release 分支；当前阶段不建议一开始把流程设计得过重。

例如：

```powershell
git checkout -b feature/platform-api
```

### 2.3 代码修改的标准流程

以后修改任意一个模块，统一按这个顺序执行：

1. 在本地 IDE 修改代码
2. 在本地完成自测
3. 提交 Git
4. push 到 GitHub
5. 服务器执行 `git pull`
6. 重装依赖或执行部署脚本
7. 重启对应服务

### 2.4 标准 Git 命令流程

```powershell
cd C:\TA\jenkins_robotframework
git status
git add .
git commit -m "feat: update kpi portal workflow"
git push origin feature/platform-api
```

如果直接同步到主线：

```powershell
git checkout main
git pull origin main
git merge feature/platform-api
git push origin main
```

### 2.5 服务器同步代码的标准方式

服务器第一次部署：

**服务器动作标签**：`允许做 / 代码同步 / git clone + chown`

```bash
cd /opt
sudo git clone https://github.com/stella555359/jenkins_robotframework.git
sudo chown -R ute:ute /opt/jenkins_robotframework
```

解释：

- `git clone` 用于首次把仓库代码同步到服务器
- `chown` 用于把仓库 ownership 调整为日常操作用户 `ute`
- 这里同步的是 Git 仓库代码，不是在服务器上手工创建业务源码

如果服务器访问 GitHub 需要走公司代理，可改用一次性代理方式执行克隆：

**服务器动作标签**：`允许做 / 代码同步 / git clone with proxy`

```bash
cd /opt
sudo git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 clone https://github.com/stella555359/jenkins_robotframework.git
sudo chown -R ute:ute /opt/jenkins_robotframework
```

这种写法只对当前这次 `git clone` 生效，不会把代理永久写入服务器上的 Git 全局配置。

如果后续执行 `git status`、`git pull` 时出现如下报错：

```text
fatal: detected dubious ownership in repository at '/opt/jenkins_robotframework'
```

优先先修正仓库目录所有权，而不是第一时间把目录加入 `safe.directory`：

**服务器动作标签**：`谨慎做 / 仓库安全修复 / chown + git status`

```bash
sudo chown -R ute:ute /opt/jenkins_robotframework
cd /opt/jenkins_robotframework
git status
```

解释：

- 先修 ownership，再验证仓库状态
- `safe.directory` 只作为例外白名单，不是默认修复方案

只有在已经确认这是预期的跨用户托管目录、并且确实需要保留当前 ownership 布局时，才额外执行：

**服务器动作标签**：`谨慎做 / 仓库安全白名单 / git config`

```bash
git config --global --add safe.directory /opt/jenkins_robotframework
```

对于当前这套部署方式，推荐原则仍然是：仓库工作区由日常操作用户 `ute` 持有，避免后续普通 Git 命令持续触发 ownership 安全检查。

### 2.5.1 服务器侧 Git 代理使用规范

推荐优先使用一次性代理参数，也就是只在当前命令上附带：

**服务器动作标签**：`允许做 / 代码同步 / git pull with proxy`

```bash
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
```

解释：

- 这是最小化影响范围的一次性代理写法
- 代理只对当前这条 Git 命令生效，不会污染后续仓库操作

适合使用一次性代理的场景：

- 只有访问 GitHub 时偶尔需要代理
- 服务器同时还要访问内网 GitLab、制品库或其他不需要代理的地址
- 希望把影响范围限制在单条命令，避免后续 Git 行为被全局代理污染

不建议默认配置 Git 全局代理的原因：

- `git config --global http.proxy ...` 会影响当前用户后续所有 Git 仓库操作
- 容易导致本来可以直连的内网仓库也被错误转发到代理
- 后续排查网络问题时，不容易第一时间看出是全局 Git 代理导致

只有在以下条件同时满足时，才考虑配置全局代理：

- 这台服务器长期只通过代理访问外部 Git 仓库
- 运维策略已经明确要求该用户所有 Git 操作统一走代理
- 已确认不会影响其他内网仓库访问

后续每次发布：

**服务器动作标签**：`允许做 / 代码同步 / git fetch + checkout + pull`

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

解释：

- `fetch` 先刷新远端状态
- `checkout main` 确保站在发布分支上
- `pull --ff-only` 只接受干净的线性更新

如果后续发布时服务器访问 GitHub 也需要走代理，则改用：

**服务器动作标签**：`允许做 / 代码同步 / git fetch + pull with proxy`

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 fetch origin
git checkout main
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
```

关于这组命令的说明：

- 如果你已经确认服务器当前一直就在 `main` 分支，并且工作区是干净的，那么可以直接执行 `git pull --ff-only origin main`
- 文档里保留 `git fetch origin` + `git checkout main` + `git pull --ff-only origin main`，是为了让发布步骤更显式、更安全，避免人在别的分支、游离 HEAD 或远程状态未刷新的情况下误操作
- `git fetch origin` 的作用是只从远端拉取最新提交信息并更新本地的远程跟踪分支，例如 `origin/main`，但不修改当前工作区文件
- `git checkout main` 的作用是明确切回目标发布分支，避免当前人在其他分支上直接 pull
- `git pull --ff-only origin main` 的本质是“先 fetch，再把当前分支快进到 `origin/main`”，其中 `--ff-only` 表示只允许快进更新，不允许自动生成 merge commit

对于当前这套服务器发布场景，推荐理解为：

1. `fetch`：先看远端最新到了哪里
2. `checkout main`：确保自己站在正确分支上
3. `pull --ff-only`：只接受干净的线性更新，不在服务器上制造额外合并提交

所以结论是：

- 日常临时手工发布，如果你非常确定自己已经在 `main`，直接 `git pull --ff-only origin main` 可以用
- 文档默认仍保留 `fetch` + `checkout` + `pull --ff-only`，因为更适合作为标准操作手册

**重点说明**：

- 服务器上不手工修改代码
- 如果服务器工作区有脏文件，先查明原因，不要直接覆盖
- 所有改动都应先回到本地仓库再提交

### 2.6 当前仓库骨架基线

当前仓库应至少包含以下三块模块骨架，第一次 push 前建议确认都已存在：

```text
jenkins-kpi-platform/
    jcasc/ jobs/ pipelines/ scripts/ vars/ resources/ templates/ docs/

kpi-portal/
    app/api/v1/ app/core/ app/models/ app/schemas/ app/services/ app/utils/
    tests/ data/uploads/ data/jobs/ data/api/ logs/ scripts/ docs/

platform-api/
    app/api/v1/ app/core/ app/models/ app/schemas/ app/services/ app/utils/
    tests/ data/uploads/ data/results/ data/exports/ logs/ scripts/ docs/
```

空目录建议保留 `.gitkeep`，Python 包目录建议至少保留 `__init__.py`，这样第一次提交时 Git 能完整跟踪项目框架。

---

## 第三步：服务器基础环境准备

### 3.1 Master 服务器基础初始化

在 10.71.210.104 上执行：

**服务器动作标签**：`允许做 / 运行环境 / apt update + apt install`

```bash
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    tree \
    unzip \
    net-tools \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    openjdk-21-jdk \
    nginx
```

解释：

- 这一步只安装操作系统层运行依赖，不创建业务源码文件
- `openjdk`、`python3`、`nginx` 等属于运行环境准备

### 3.2 创建统一部署目录

这一节的目标只是准备服务器上的运行目录和权限，不是让你在服务器上手工创建业务开发文件。

这里创建的目录只包括：

- Git 仓库的挂载位置，例如 `/opt/jenkins_robotframework`
- 运行期数据目录，例如日志、备份、数据目录
- 后续 systemd、Nginx、Jenkins 等服务会用到的宿主机目录

不应该在服务器上手工做的事情包括：

- 手工 `mkdir` 出 `app/api/v1`、`app/services` 这类业务源码目录
- 手工 `vim` / `nano` 创建 `main.py`、`router.py`、`requirements.txt` 这类开发文件
- 在服务器上先写一套源码，再和本地 GitHub 仓库分头维护

**服务器动作标签**：`允许做 / 运行目录 / mkdir`

```bash
sudo mkdir -p /opt/jenkins_robotframework
sudo mkdir -p /var/lib/jenkins-kpi-platform/{logs,backups,data}
sudo chown -R ute:ute /opt/jenkins_robotframework
sudo chown -R ute:ute /var/lib/jenkins-kpi-platform
```

解释：

- 这里只创建仓库挂载目录和运行期目录
- 这些目录属于部署宿主机资源，不属于业务源码目录

真正的业务源码进入服务器的方式应始终是：

1. 本地 IDE 开发
2. 提交到 GitHub
3. 服务器通过 `git clone` 或 `git pull` 同步

如果某些目录只是为了让 Git 能跟踪空目录，应在本地仓库里通过 `.gitkeep` 或 `__init__.py` 处理，然后随仓库一起同步到服务器，而不是在服务器上单独补建。

### 3.2.1 当前阶段服务器上允许手工创建的内容

当前文档允许在服务器上手工创建的，主要是这几类非业务源码内容：

- 操作系统层目录
- Python 虚拟环境
- systemd service 文件
- Nginx 配置文件
- Jenkins 运行相关配置

这些内容属于部署与运行环境配置，不属于日常业务开发源码。

### 3.2.2 服务器上哪些能手工建，哪些绝不能手工建

| 项目 | 是否允许在服务器上手工创建 | 类型 | 说明 |
|---|---|---|---|
| `/opt/jenkins_robotframework` | 允许 | 运行目录 | 只是仓库挂载位置，源码仍通过 Git 同步进入 |
| `/var/lib/jenkins-kpi-platform/...` | 允许 | 运行目录 | 日志、备份、数据等运行期目录 |
| `venv` 虚拟环境 | 允许 | 运行环境 | 属于服务器本地运行环境，不属于源码仓库主体 |
| `/etc/systemd/system/*.service` | 允许 | 运行配置文件 | 用于服务启动和守护 |
| `/etc/nginx/sites-available/*.conf` | 允许 | 运行配置文件 | 用于反向代理和 HTTPS |
| Jenkins drop-in / JCasC 落地配置 | 允许 | 运行配置文件 | 属于 Jenkins 运行配置 |
| `/etc/sudoers.d/jenkins` | 允许 | 运行配置文件 | 属于系统权限配置 |
| `app/main.py` | 不允许 | 业务源码文件 | 必须在本地开发后随 Git 同步 |
| `app/api/v1/router.py` | 不允许 | 业务源码文件 | 必须进入 Git 历史 |
| `requirements.txt` | 不允许 | 业务源码文件 | 依赖清单应由本地仓库维护 |
| `.env.example` | 不允许在服务器上手工作为源码创建 | 业务源码文件 | 示例文件应在本地仓库维护 |
| `tests/*` | 不允许 | 业务源码文件 | 测试代码必须由本地开发和提交管理 |
| `app/services/*`、`app/schemas/*` | 不允许 | 业务源码文件 | 业务逻辑代码不在服务器直接编写 |

判断规则可以简单记成：

- 和操作系统、服务启动、代理转发、运行环境有关的，可以在服务器上手工创建
- 和业务逻辑、接口实现、依赖清单、测试代码有关的，不能在服务器上手工创建

### 3.2.3 服务器动作分类总表

这张总表已经前移到 [服务器动作执行总原则](#13-服务器动作执行总原则)。第三步开始默认继承那里定义的标签与分类。

### 3.3 Agent 服务器基础配置

在 10.57.159.149 上执行：

**服务器动作标签**：`允许做 / 运行环境与运行配置 / apt install + tee + mkdir`

```bash
sudo apt update
sudo apt upgrade -y

sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    openjdk-21-jre \
    git \
    openssh-server \
    curl \
    vim

sudo useradd -m -s /bin/bash jenkins || true
echo "jenkins ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/jenkins

sudo mkdir -p /automation/{workspace,venv,logs,downloads}
sudo chown -R jenkins:jenkins /automation
```

解释：

- `/etc/sudoers.d/jenkins` 属于 `运行配置文件`
- `/automation/...` 属于 `运行目录`
- 这段命令不涉及业务源码文件创建

### 3.4 SSH 免密配置

Master 上生成密钥：

**服务器动作标签**：`允许做 / 运行配置文件 / ssh-keygen + authorized_keys`

```bash
ssh-keygen -t rsa -b 4096 -C "jenkins-master" -f ~/.ssh/jenkins_agent_rsa -N ""
```

将公钥加入 Agent 的 `authorized_keys` 后验证：

**服务器动作标签**：`允许做 / 运行配置验证 / ssh`

```bash
ssh -i ~/.ssh/jenkins_agent_rsa jenkins@10.57.159.149 "echo 'SSH OK'"
```

解释：

- `authorized_keys` 属于 `运行配置文件`
- SSH 密钥用于访问控制，不属于业务源码
- `ssh ... "echo 'SSH OK'"` 属于连通性验证动作

---

## 第四步：Jenkins Master 部署

### 4.1 安装 Jenkins

**服务器动作标签**：`允许做 / 运行配置文件 / tee`

```bash
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io.key

echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | \
  sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt update
sudo apt install -y jenkins
```

解释：

- `/etc/apt/sources.list.d/jenkins.list` 属于 `运行配置文件`
- 这一步是在安装 Jenkins 运行依赖，不是在维护业务源码

### 4.2 启动 Jenkins

**服务器动作标签**：`谨慎做 / 服务控制 / systemctl`

```bash
sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo systemctl status jenkins
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

解释：

- `systemctl enable/start/status` 属于服务控制动作
- 应在确认安装完成且配置正确后执行

### 4.3 初始化 Jenkins Web

建议通过 SSH 隧道访问，不直接暴露 8080：

```powershell
ssh -L 8080:localhost:8080 ute@10.71.210.104
```

然后本地浏览器访问：

```text
http://localhost:8080
```

### 4.4 配置 Jenkins 子路径和外部访问地址

因为后续会通过 Nginx 以 `/jenkins/` 路径反向代理，所以要先把 Jenkins 自身配置为带前缀运行，避免静态资源和跳转链接错误。

在 Master 服务器执行：

**服务器动作标签**：`谨慎做 / 运行配置文件 / systemctl edit`

```bash
sudo systemctl edit jenkins
```

解释：

- 这里创建的是 Jenkins 的 systemd drop-in 配置
- 它属于 `运行配置文件`，不是业务源码文件

写入以下内容：

**服务器动作标签**：`允许做 / 运行配置文件 / systemd drop-in` 

```ini
[Service]
Environment="JENKINS_PREFIX=/jenkins"
```

解释：

- 这段内容用于让 Jenkins 以 `/jenkins` 子路径运行
- 它属于运行配置内容，不属于仓库业务源码

保存后执行：

**服务器动作标签**：`谨慎做 / 服务控制 / systemctl`

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

解释：

- `daemon-reload` 让 systemd 重新加载 drop-in 配置
- `restart` 和 `status` 用于使新配置生效并确认服务状态

先不要急着修改 Jenkins Web 里的 `Jenkins URL`，继续按下面的 `4.7`、`4.8`、`4.9` 完成 HTTPS 和外部访问验证后，再回到 Jenkins 中设置最终外部地址。

### 4.5 Jenkins 必装插件

- Pipeline
- Git
- Credentials Binding
- SSH Build Agents
- Configuration as Code
- Timestamper
- AnsiColor
- HTML Publisher
- JUnit

### 4.6 Jenkins 的定位

Jenkins 在这个方案中的职责不是“让你在服务器写代码”，而是：

- 从 GitHub 拉取代码
- 执行部署脚本
- 同步 `robotws` / `testline_configuration` 等依赖仓库
- 触发测试和报告生成流程

### 4.7 证书准备

如果你当前还没有正式域名，不能直接用 Let's Encrypt 给 IP 地址签发证书。此时建议先用以下两种方式之一：

- 公司内部 CA 证书
- 临时自签名证书（仅内网测试）

先生成一份可测试的自签名证书：

**服务器动作标签**：`允许做 / 运行配置文件 / openssl req`

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
  -keyout /etc/ssl/private/jenkins-kpi-platform.key \
  -out /etc/ssl/certs/jenkins-kpi-platform.crt \
  -subj "/CN=10.71.210.104"
```

解释：

- 证书和私钥文件属于运行配置资产，不属于业务源码
- 这一步用于先打通 Jenkins 的 HTTPS 测试链路

如果后续拿到了正式域名，再切换到公司签发证书或 Let's Encrypt。

### 4.8 Jenkins 的 Nginx 反向代理与 HTTPS 配置

建议由 Nginx 先把 Jenkins 的外部入口固定为 `/jenkins/`，这样后面你从 Windows 访问、设置 Jenkins URL、再接 Portal 服务时，入口结构都是一致的。

这一段最容易误解的地方是：下面这大段 `server { ... }` 不是命令，而是 **Nginx 配置文件的内容**。

你现在可以直接按下面这个顺序做：

1. 先在本地仓库里准备一个 Nginx 配置文件
2. 这个文件路径建议就是：`deploy/nginx/jenkins-kpi-platform.conf`
3. 把下面这段 `server { ... }` 原样写进这个文件
4. 再把这个文件复制到服务器的 `/etc/nginx/sites-available/jenkins-kpi-platform.conf`
5. 最后执行 `nginx -t` 和 `systemctl restart nginx`

也就是说：

- `server { ... }` 这段内容不是贴到 Jenkins 里
- 也不是直接在终端里执行
- 它是要保存成一个 `.conf` 文件，再交给 Nginx 读取

建议先在仓库新建文件：

```text
deploy/nginx/jenkins-kpi-platform.conf
```

文件内容如下：

**服务器动作标签**：`允许做 / 运行配置文件 / nginx conf`

```nginx
server {
    listen 80;
    server_name 10.71.210.104;

    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name 10.71.210.104;

    ssl_certificate /etc/ssl/certs/jenkins-kpi-platform.crt;
    ssl_certificate_key /etc/ssl/private/jenkins-kpi-platform.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    location /jenkins/ {
        proxy_pass http://127.0.0.1:8080/jenkins/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
    }

    location /kpi/ {
        proxy_pass http://127.0.0.1:8001/;
    }
}
```

解释：

- 这段 Nginx 配置属于 `运行配置文件`
- 它定义的是 Jenkins 和后续 Portal 服务的统一外部访问入口，不属于业务源码实现

如果你当前仓库里还没有这个文件，就先在本地 IDE 中创建它；后续这个文件也应该跟代码一起进入 Git 管理。

启用配置：

**服务器动作标签**：`允许做 / 运行配置文件 / cp`

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf /etc/nginx/sites-available/jenkins-kpi-platform.conf
sudo ln -sf /etc/nginx/sites-available/jenkins-kpi-platform.conf /etc/nginx/sites-enabled/jenkins-kpi-platform.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

解释：

- `cp` 负责把仓库中的部署配置落地到系统目录
- `systemctl restart nginx` 属于服务控制动作，应在 `nginx -t` 通过后执行
- `/etc/nginx/sites-available/jenkins-kpi-platform.conf` 才是服务器上真正被 Nginx 读取的位置
- 仓库里的 `deploy/nginx/jenkins-kpi-platform.conf` 是你维护这份配置的源码位置

这里有一个非常容易漏掉的点：

- **只把文件放进 `sites-available/` 还不够**
- **必须再把它链接到 `sites-enabled/`，Nginx 才会真正加载它**

也就是说，如果你已经能看到：

```text
/etc/nginx/sites-available/jenkins-kpi-platform.conf
```

但 `sudo ls -l /etc/nginx/sites-enabled` 里仍然只有 `default`，没有 `jenkins-kpi-platform.conf` 的符号链接，那么当前这份 HTTPS 配置其实还没有生效。

这种情况下的典型现象就是：

- `nginx.service` 看起来是 `active (running)`
- `nginx -t` 也显示语法正常
- 但 `ss -lntp | grep :443` 没有结果
- `curl -k -I https://127.0.0.1/jenkins/` 仍然连不上

修复方式就是把站点真正启用起来：

```bash
sudo ln -sf /etc/nginx/sites-available/jenkins-kpi-platform.conf /etc/nginx/sites-enabled/jenkins-kpi-platform.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

然后立刻复查：

```bash
sudo ss -lntp | grep :443
curl -k -I https://127.0.0.1/jenkins/
```

如果这时 `443` 已经开始监听，说明问题根因就是“配置文件放到了 `sites-available`，但没有真正启用到 `sites-enabled`”。

如果这里执行 `cp` 时出现：

```text
cp: cannot create regular file '/etc/nginx/sites-available/jenkins-kpi-platform.conf': No such file or directory
```

说明当前服务器上的 Nginx 配置目录布局不是常见的 Debian `sites-available / sites-enabled` 结构。此时不要直接怀疑配置内容本身，先检查服务器上的 Nginx 实际目录：

```bash
sudo nginx -v
sudo systemctl status nginx
sudo ls -l /etc/nginx
```

常见处理方式有两种：

1. 如果只是缺少 `sites-available` 和 `sites-enabled` 目录，但当前 Nginx 仍按 Debian 方式加载这些目录，可以先手工创建：

```bash
sudo mkdir -p /etc/nginx/sites-available
sudo mkdir -p /etc/nginx/sites-enabled
```

然后再继续执行 `cp`、`ln -sf`、`nginx -t`、`systemctl restart nginx`。

2. 如果这台机器的 Nginx 实际使用的是 `/etc/nginx/conf.d/`，那就不要继续套用 `sites-available` 路径，而应改为：

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf /etc/nginx/conf.d/jenkins-kpi-platform.conf
sudo nginx -t
sudo systemctl restart nginx
```

判断标准很简单：先看 `/etc/nginx/nginx.conf` 里到底 `include` 了哪类目录，再决定用 `sites-available` 还是 `conf.d`。

如果你执行 `sudo ls -l /etc/nginx` 后看到的是：

```text
total 0
```

那问题就比“少一个 `sites-available` 目录”更进一步了。这通常说明：

- Nginx 包并没有正常安装完成
- 或者 `/etc/nginx` 里的默认配置文件被清空了
- 或者当前机器上的 Nginx 环境还没真正准备好

这种情况下，不建议继续手工只补一个 `sites-available` 目录，因为连 `nginx.conf` 这样的主配置入口都还不存在。更稳妥的处理顺序是：

```bash
sudo nginx -v
sudo systemctl status nginx
dpkg -l | grep nginx
sudo apt install --reinstall -y nginx
sudo ls -l /etc/nginx
```

预期你至少应该重新看到类似这些内容：

- `/etc/nginx/nginx.conf`
- `/etc/nginx/conf.d/`
- `/etc/nginx/sites-available/` 或其他发行版默认目录

只有当这些基础文件恢复后，才继续复制 `jenkins-kpi-platform.conf` 并执行 `nginx -t`。

如果你不想直接重装，也至少先确认这两件事：

1. `nginx` 命令是否真实存在
2. `systemctl status nginx` 指向的服务是不是你预期的那个 Nginx

因为 `total 0` 这种结果本身就说明当前机器的 Nginx 基础状态不正常，还没进入“部署反向代理配置文件”这一步。

如果你进一步检查后看到的是：

```text
sudo: nginx: command not found
Unit nginx.service could not be found.
```

那就可以直接下结论：**这台机器当前并没有安装好 Nginx**。

这时不要再继续排查 `sites-available`、`conf.d`、`nginx.conf` 这些目录细节，因为问题还停留在更前面的安装阶段。正确处理顺序应改为：

```bash
sudo apt update
sudo apt install -y nginx
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx
sudo ls -l /etc/nginx
```

如果安装过程中报包损坏、依赖缺失或 dpkg 中断，再补执行：

```bash
sudo dpkg --configure -a
sudo apt -f install
sudo apt install -y nginx
```

只有当下面这些条件成立后，才继续本节后面的代理配置步骤：

1. `sudo nginx -v` 可以返回版本号
2. `sudo systemctl status nginx` 能看到服务状态
3. `/etc/nginx/nginx.conf` 已存在

然后再继续复制：

```bash
sudo cp /opt/jenkins_robotframework/deploy/nginx/jenkins-kpi-platform.conf /etc/nginx/sites-available/jenkins-kpi-platform.conf
```

或者根据实际目录结构改为复制到 `conf.d/`。

### 4.9 从 Windows 验证外部访问并设置 Jenkins URL

先在服务器上做基础验证：

**服务器动作标签**：`允许做 / 运维检查 / curl health and headers`

```bash
curl -k -I https://10.71.210.104/jenkins/
curl -k -I https://10.71.210.104/api/health
curl -k -I https://10.71.210.104/kpi/health
```

解释：

- 这组命令用于检查 HTTPS、Nginx 反代和服务健康接口是否已经联通
- 它们只读取结果，不会修改服务器状态

如果这里执行：

```bash
curl -k -I https://10.71.210.104/jenkins/
```

返回：

```text
curl: (7) Failed to connect to 10.71.210.104 port 443 after 0 ms: Could not connect to server
```

说明当前问题不是 Jenkins 路径 `/jenkins/` 配错了，而是服务器这一层还没有成功对外提供 `443` HTTPS 入口。常见根因通常只有这几类：

1. Nginx 还没有启动
2. Nginx 启动了，但没有成功监听 `443`
3. 服务器防火墙、安全组或网络策略挡住了 `443`

这时先不要继续纠结 Jenkins URL，而要先检查最底层的 `443` 监听状态。推荐按下面顺序排查：

```bash
sudo systemctl status nginx
sudo ss -lntp | grep :443
sudo nginx -t
sudo journalctl -u nginx -n 100
curl -k -I https://127.0.0.1/jenkins/
```

判断方法：

- 如果 `systemctl status nginx` 显示服务没启动，先解决 Nginx 启动问题
- 如果 `ss -lntp | grep :443` 没有结果，说明当前机器上没有进程监听 `443`
- 如果 `curl -k -I https://127.0.0.1/jenkins/` 在服务器本机也失败，说明问题在 Nginx/证书/监听配置本身
- 如果服务器本机能通 `https://127.0.0.1/jenkins/`，但访问 `https://10.71.210.104/jenkins/` 不通，那就优先怀疑防火墙或网络路径

如果进一步出现下面这种组合现象：

- `curl -k -L https://127.0.0.1/jenkins/` 已经能看到 Jenkins 登录跳转页内容
- 但 Windows 浏览器访问 `https://10.71.210.104/jenkins/` 最终显示 `404 Not Found`

那通常说明问题已经不在 Nginx 监听层，而在 **Jenkins 自己并没有真正按 `/jenkins` 子路径运行**。

典型信号包括：

- 页面里跳转到了 `/login?from=%2Fjenkins%2F`
- 静态资源路径看起来像 `/static/...`
- 响应头里仍然出现 `http://10.71.210.104:8080/...` 这样的根路径或旧地址

这类现象的本质是：

1. Nginx 已经把 `/jenkins/` 请求送到了 Jenkins
2. 但 Jenkins 返回的页面内容里仍然把自己当成“挂在根路径 `/` 下”
3. 浏览器随后去请求 `/login`、`/static/...` 这类根路径
4. 而你的 Nginx 只配置了 `/jenkins/` 转发，所以浏览器最终看到 `404 Not Found`

这时应优先检查 Jenkins Prefix 是否真的生效：

```bash
sudo systemctl cat jenkins
sudo systemctl show jenkins --property=Environment
curl -I http://127.0.0.1:8080/jenkins/
curl -I http://127.0.0.1:8080/login
```

如果 `systemctl show jenkins --property=Environment` 里没有看到：

```text
JENKINS_PREFIX=/jenkins
```

说明前面写入的 drop-in 配置还没有真正生效，需要回到 `4.4` 重新确认 `systemctl edit jenkins` 的内容，然后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

如果你已经实际验证到下面这种结果：

- `sudo systemctl show jenkins --property=Environment` 里 **没有** `JENKINS_PREFIX=/jenkins`
- `curl -I http://127.0.0.1:8080/jenkins/` 返回 `403 Forbidden`
- `curl -I http://127.0.0.1:8080/login` 返回 `200 OK`

那就可以直接确认：

**当前 Jenkins 仍然是在根路径 `/` 下运行，`/jenkins` 前缀配置并没有真正生效。**

这时最稳妥的修复方式，不是再进交互式编辑器猜 drop-in 是否保存成功，而是直接把 override 文件明确写到 systemd 目录里：

```bash
sudo mkdir -p /etc/systemd/system/jenkins.service.d
sudo tee /etc/systemd/system/jenkins.service.d/override.conf > /dev/null << 'EOF'
[Service]
Environment="JENKINS_PREFIX=/jenkins"
EOF
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl show jenkins --property=Environment
```

修复后，目标是重新看到：

```text
JENKINS_PREFIX=/jenkins
```

然后立刻复查：

```bash
curl -I http://127.0.0.1:8080/jenkins/
curl -I http://127.0.0.1:8080/login
curl -k -L https://10.71.210.104/jenkins/
```

如果 Prefix 生效，后续浏览器访问 `https://10.71.210.104/jenkins/` 时就不应该再因为跳到根路径 `/login` 而落成 `404 Not Found`。

然后回到 Windows 浏览器访问：

```text
https://10.71.210.104/jenkins/
```

如果当前使用的是自签名证书，浏览器先出现证书告警是正常现象；此时你的目标是先确认 Jenkins 登录页已经能通过 HTTPS 和 `/jenkins/` 子路径稳定打开。

确认 Windows 访问正常后，再在 Jenkins Web 中设置：

- `Manage Jenkins` -> `System`
- `Jenkins URL` 改为 `https://10.71.210.104/jenkins/`

如果后面申请到了正式域名，则改为：

- `https://jenkins.company.com/jenkins/`

---

## 第五步：三块代码的开发与部署方式

这一章是本次修订的重点。

### 5.1 总原则

对于 `jenkins-kpi-platform`、`kpi-portal`、`platform-api`：

- **代码编写地点**：本地 IDE
- **版本管理地点**：GitHub 仓库 `jenkins_robotframework`
- **服务器动作**：只做 `git pull`、安装依赖、重启服务

**不允许的方式**：

- 直接 SSH 到 Debian 服务器后用 `vim` 或 `nano` 长期维护业务代码
- 服务器和 GitHub 分别维护两套不同版本
- 在服务器改了代码却不提交 Git

---

### 5.2 jenkins-kpi-platform 的开发与部署

`jenkins-kpi-platform` 建议放置 Jenkins 相关的配置和自动化资产，例如：

- `JCasC` 配置
- `Jenkinsfile`
- Job DSL
- 部署脚本
- 与 `robotws`、`testline_configuration` 集成的调度逻辑

#### 本地开发流程

```powershell
cd C:\TA\jenkins_robotframework
git checkout -b feature/jenkins-kpi-platform-update
```

在本地 IDE 修改：

- `jenkins-kpi-platform/jcasc/`
- `jenkins-kpi-platform/pipelines/`
- `jenkins-kpi-platform/scripts/`

提交并推送：

```powershell
git add .
git commit -m "feat: update jenkins kpi platform config"
git push origin feature/jenkins-kpi-platform-update
```

合并到 `main` 后，服务器同步：

**服务器动作标签**：`允许做 / 代码同步 / git fetch + checkout + pull`

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

解释：

- 这是 Jenkins 配置类变更进入服务器的标准同步动作
- 只同步仓库代码，不在服务器直接编辑 Jenkins 相关源码

如果该服务器同步 GitHub 时需要走代理，则执行：

**服务器动作标签**：`允许做 / 代码同步 / git fetch + pull with proxy`

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 fetch origin
git checkout main
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
```

解释：

- 代理只附着在当前同步命令上
- 适合这台服务器只在访问 GitHub 时临时需要代理的场景

如果包含 Jenkins 配置更新，可执行：

**服务器动作标签**：`谨慎做 / 服务控制 / systemctl restart`

```bash
sudo systemctl restart jenkins
```

解释：

- 这里只重启 Jenkins 服务，不修改业务源码
- 仅在维护窗口或明确需要刷新 Jenkins 自身配置时执行

但这类重启只建议在以下场景执行：

- 手工发布窗口
- 修改了 JCasC、插件、Jenkins Prefix 等 Jenkins 自身配置

如果是 Jenkins 自己触发的自动部署任务，不要在同一条流水线里重启 Jenkins 本体。

#### 推荐做法

- Jenkins 的配置尽量代码化，存放在仓库中
- 部署脚本也放在仓库中，不要散落在服务器各目录
- 所有 Jenkins 变更都有 commit 历史

#### 建议的初始文件骨架

第一次建仓时，`jenkins-kpi-platform` 建议至少包含：

```text
jenkins-kpi-platform/
├── jcasc/jenkins.yaml
├── jobs/README.md
├── pipelines/deploy_portals.groovy
├── scripts/deploy_jenkins_config.sh
├── vars/.gitkeep
├── resources/.gitkeep
├── templates/.gitkeep
└── docs/.gitkeep
```

---

### 5.3 platform-api 的开发与部署

`platform-api` 是业务应用代码，开发流程应完全在本地完成。

#### 本地开发

```powershell
cd C:\TA\jenkins_robotframework
git checkout -b feature/platform-api
cd platform-api
```

在本地 IDE 中：

- 编写 FastAPI 代码
- 修改 `requirements.txt`
- 编写或更新测试
- 本地运行验证接口

建议先从以下骨架开始：

```text
platform-api/
├── app/main.py
├── app/core/config.py
├── app/api/v1/router.py
├── app/services/health_service.py
├── app/schemas/health.py
├── tests/test_health.py
├── .env.example
└── requirements.txt
```

完成后提交：

```powershell
cd C:\TA\jenkins_robotframework
git add .
git commit -m "feat: update platform api"
git push origin feature/platform-api
```

#### 服务器部署

服务器不再手工创建每个源码文件，而是直接同步仓库代码：

**服务器动作标签**：`允许做 / 代码同步 / git fetch + checkout + pull`

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

解释：

- Portal 代码通过 Git 同步进入服务器
- 不在服务器上手工创建 `app/*.py`、`requirements.txt` 等业务源码文件

如果服务器访问 GitHub 需要经过代理，则改用：

**服务器动作标签**：`允许做 / 代码同步 / git fetch + pull with proxy`

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 fetch origin
git checkout main
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
```

为 `platform-api` 单独创建虚拟环境：

**服务器动作标签**：`允许做 / 运行环境 / python3 -m venv`

```bash
cd /opt/jenkins_robotframework/platform-api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

解释：

- `venv` 属于服务器本地运行环境，不属于业务源码
- 依赖安装仍以仓库中的 `requirements.txt` 为准

创建 systemd 服务：

**服务器动作标签**：`允许做 / 运行配置文件 / tee`

```bash
sudo tee /etc/systemd/system/platform-api.service > /dev/null << 'EOF'
[Unit]
Description=Platform API Service
After=network.target

[Service]
Type=simple
User=ute
WorkingDirectory=/opt/jenkins_robotframework/platform-api
Environment="PATH=/opt/jenkins_robotframework/platform-api/venv/bin"
ExecStart=/opt/jenkins_robotframework/platform-api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable platform-api
sudo systemctl restart platform-api
sudo systemctl status platform-api
```

解释：

- `platform-api.service` 属于 `运行配置文件`
- `daemon-reload`、`enable`、`restart`、`status` 属于让服务注册并生效的运行动作

发布新版本时通常只需要：

**服务器动作标签**：`允许做 / 发布更新 / git pull + pip install + systemctl restart`

```bash
cd /opt/jenkins_robotframework
git pull --ff-only origin main
cd platform-api
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart platform-api
```

解释：

- `git pull` 更新代码
- `pip install -r requirements.txt` 更新运行依赖
- `systemctl restart` 让新版本生效

如果该服务器对 GitHub 需要代理，则改用：

**服务器动作标签**：`允许做 / 发布更新 / git pull with proxy + pip install + restart`

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
cd platform-api
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart platform-api
```

解释：

- 与非代理版本相同，只是把 Git 同步改成一次性代理写法
- 依赖安装和服务重启流程保持不变

---

### 5.4 kpi-portal 的开发与部署

`kpi-portal` 同样采用本地开发、GitHub 管理、服务器拉取的模式。

#### 本地开发

```powershell
cd C:\TA\jenkins_robotframework
git checkout -b feature/kpi-portal
cd kpi-portal
```

本地完成以下工作：

- API 代码开发
- 与 `kpi-anomaly-detector`、`kpi-generator` 的集成代码编写
- 参数校验、任务管理、接口测试
- 依赖文件维护

建议先从以下骨架开始：

```text
kpi-portal/
├── app/main.py
├── app/core/config.py
├── app/api/v1/router.py
├── app/services/health_service.py
├── app/schemas/health.py
├── tests/test_health.py
├── .env.example
└── requirements.txt
```

提交并推送：

```powershell
cd C:\TA\jenkins_robotframework
git add .
git commit -m "feat: update kpi portal"
git push origin feature/kpi-portal
```

#### 服务器部署

**服务器动作标签**：`允许做 / 代码同步 / git fetch + checkout + pull`

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

解释：

- KPI Portal 与 Platform API 的服务器同步原则一致
- 服务器只同步代码并安装依赖，不直接维护业务源码

如果服务器访问 GitHub 需要经过代理，则改用：

**服务器动作标签**：`允许做 / 代码同步 / git fetch + pull with proxy`

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 fetch origin
git checkout main
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
```

解释：

- KPI Portal 的代理同步方式与 Platform API 完全一致
- 这样可以保持服务器发布流程统一

安装依赖：

**服务器动作标签**：`允许做 / 运行环境 / python3 -m venv`

```bash
cd /opt/jenkins_robotframework/kpi-portal
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

解释：

- 这一步准备 KPI Portal 独立虚拟环境
- 运行环境与业务源码分离，便于后续部署维护

创建 systemd 服务：

**服务器动作标签**：`允许做 / 运行配置文件 / tee`

```bash
sudo tee /etc/systemd/system/kpi-portal.service > /dev/null << 'EOF'
[Unit]
Description=KPI Portal Service
After=network.target

[Service]
Type=simple
User=ute
WorkingDirectory=/opt/jenkins_robotframework/kpi-portal
Environment="PATH=/opt/jenkins_robotframework/kpi-portal/venv/bin"
ExecStart=/opt/jenkins_robotframework/kpi-portal/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable kpi-portal
sudo systemctl restart kpi-portal
sudo systemctl status kpi-portal
```

解释：

- `kpi-portal.service` 也属于 `运行配置文件`
- 这里是在注册和启动服务，而不是创建业务源码文件

后续版本发布：

**服务器动作标签**：`允许做 / 发布更新 / git pull + pip install + systemctl restart`

```bash
cd /opt/jenkins_robotframework
git pull --ff-only origin main
cd kpi-portal
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart kpi-portal
```

解释：

- 与 Platform API 相同，动作顺序是更新代码、更新依赖、重启服务
- 这属于运行发布动作，不属于开发动作

如果该服务器对 GitHub 需要代理，则改用：

**服务器动作标签**：`允许做 / 发布更新 / git pull with proxy + pip install + restart`

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
cd kpi-portal
source venv/bin/activate
pip install -r requirements.txt
deactivate
sudo systemctl restart kpi-portal
```

解释：

- 代理版本只改变 Git 拉取方式
- 后续依赖刷新和服务重启仍按标准发布动作执行

---

### 5.5 三块代码的统一发布原则

推荐把发布动作固化成脚本，例如：

**服务器动作标签**：`允许做 / 发布脚本 / git pull + pip install + restart`

```bash
#!/usr/bin/env bash
set -e

cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main

cd /opt/jenkins_robotframework/platform-api
source venv/bin/activate
pip install -r requirements.txt
deactivate

cd /opt/jenkins_robotframework/kpi-portal
source venv/bin/activate
pip install -r requirements.txt
deactivate

sudo systemctl restart platform-api
sudo systemctl restart kpi-portal
```

解释：

- 脚本把标准发布动作固化，减少手工漏步骤
- 推荐脚本受 Git 管理，避免服务器上散落无版本控制的部署脚本

如果部署机访问 GitHub 必须经过代理，则脚本中的 Git 同步部分可改成：

**服务器动作标签**：`允许做 / 发布脚本 / git pull with proxy`

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 fetch origin
git checkout main
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
```

解释：

- 如果脚本运行环境访问 GitHub 需要代理，只替换 Git 同步部分即可
- 脚本里其他依赖安装和服务重启动作无需额外改写

这个脚本也应纳入 GitHub 仓库管理，例如放在：

```text
deploy/scripts/deploy_all.sh
```

这样以后任何部署逻辑变更也有版本记录。

**重要说明**：

- `deploy_all.sh` 默认只重启 `platform-api` 和 `kpi-portal`
- 不要在 Jenkins 触发自己的部署任务时顺便重启 Jenkins
- 如果确实需要更新 Jenkins 自身配置，建议单独准备 `deploy_jenkins_config.sh`，并在维护窗口手工执行

---

## 第六步：Jenkins Agent 配置

### 6.1 Agent 节点用途

Agent 节点主要负责：

- 拉取测试相关仓库
- 执行 `robotws` 自动化任务
- 调用测试线资源
- 生成测试结果
- 将结果推送给 `platform-api` 或 `kpi-portal`

### 6.2 在 Jenkins 中添加 Agent

在 Jenkins Web 中：

1. Manage Jenkins
2. Nodes
3. New Node
4. 选择 Permanent Agent

建议配置：

- Name: `t813-agent`
- Remote root directory: `/automation/workspace`
- Labels: `t813 robot`
- Launch method: `Launch agents via SSH`
- Host: `10.57.159.149`
- Credentials: Jenkins 中配置的 SSH 凭据

### 6.3 Agent 侧代码同步原则

Agent 上运行的测试仓库，例如 `robotws`、`testline_configuration`，仍然可以由 Jenkins Job 在构建时拉取。

但 `jenkins-kpi-platform`、`kpi-portal`、`platform-api` 的业务代码主线仍以 GitHub 仓库为准，不在 Agent 上手工维护。

---

## 第七步：Pipeline 与代码同步流程

### 7.1 推荐的发布链路

以后建议采用下面这条标准链路：

1. 本地 IDE 修改代码
2. push 到 GitHub `jenkins_robotframework`
3. Jenkins 监听 GitHub 变更或手工触发
4. Jenkins 在 Master 上执行部署脚本
5. 服务器 `git pull` 最新代码
6. 重装依赖
7. 重启服务
8. 执行健康检查

### 7.2 最小可用部署 Pipeline

**服务器动作标签**：`谨慎做 / 自动化发布 / Jenkins Pipeline ssh + git pull + pip install + restart`

```groovy
pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main', url: 'https://github.com/stella555359/jenkins_robotframework.git'
            }
        }

        stage('Deploy To Master') {
            steps {
                sh '''
                ssh ute@10.71.210.104 '
                    set -e
                    cd /opt/jenkins_robotframework
                    git fetch origin
                    git checkout main
                    git pull --ff-only origin main

                    cd /opt/jenkins_robotframework/platform-api
                    . venv/bin/activate
                    pip install -r requirements.txt
                    deactivate

                    cd /opt/jenkins_robotframework/kpi-portal
                    . venv/bin/activate
                    pip install -r requirements.txt
                    deactivate

                    sudo systemctl restart platform-api
                    sudo systemctl restart kpi-portal
                '
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                ssh ute@10.71.210.104 '
                    curl --noproxy localhost http://localhost:8000/health
                    curl --noproxy localhost http://localhost:8001/health
                '
                '''
            }
        }
    }
}
```

解释：

- 这里是 Jenkins 通过 SSH 在服务器执行标准发布动作
- Pipeline 只应该编排“同步代码、安装依赖、重启服务”，不应演变成服务器直接开发入口

如果 Master 服务器访问 GitHub 也需要公司代理，则 `Deploy To Master` 阶段中的 Git 同步命令改成：

**服务器动作标签**：`谨慎做 / 自动化发布 / Jenkins Pipeline with proxy`

```groovy
ssh ute@10.71.210.104 '
    set -e
    cd /opt/jenkins_robotframework
    git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 fetch origin
    git checkout main
    git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main

    cd /opt/jenkins_robotframework/platform-api
    . venv/bin/activate
    pip install -r requirements.txt
    deactivate

    cd /opt/jenkins_robotframework/kpi-portal
    . venv/bin/activate
    pip install -r requirements.txt
    deactivate

    sudo systemctl restart platform-api
    sudo systemctl restart kpi-portal
'
```

解释：

- 这是 Pipeline 中代理版的远程发布片段
- 只替换 Git 同步命令，其余发布步骤与标准 Pipeline 保持一致

### 7.3 手工发布与自动发布的关系

初期可以先手工发布：

- 本地 push 到 GitHub
- 手工 SSH 到服务器执行 `git pull`

稳定后再切到 Jenkins 自动发布。

这两种方式的代码源都必须保持一致，都是 GitHub 仓库。

---

## 第八步：验证与日常运维

### 8.1 每次发布后的检查项

- [ ] GitHub 上目标分支代码已更新
- [ ] 服务器 `git pull` 成功
- [ ] `platform-api` 依赖安装成功
- [ ] `kpi-portal` 依赖安装成功
- [ ] Jenkins / KPI Portal / Platform API 服务状态正常
- [ ] `/health` 接口正常

### 8.2 常用检查命令

**服务器动作标签**：`允许做 / 运维检查 / git log + git status + systemctl status + curl`

```bash
cd /opt/jenkins_robotframework
git log -1 --oneline
git status

sudo systemctl status jenkins
sudo systemctl status platform-api
sudo systemctl status kpi-portal

curl --noproxy localhost http://localhost:8000/health
curl --noproxy localhost http://localhost:8001/health
```

解释：

- 这组命令只用于检查代码版本、服务状态和健康接口
- 属于读状态动作，不会修改业务源码或部署配置

### 8.3 回滚方式

如果新版本有问题，不要在服务器直接改代码，应该回滚 Git 版本。

**推荐回滚方式**：在本地仓库生成回滚提交，再同步到服务器。

例如在本地执行：

```powershell
cd C:\TA\jenkins_robotframework
git log --oneline
git revert <problem_commit>
git push origin main
```

然后在服务器执行：

**服务器动作标签**：`谨慎做 / 回滚发布 / git fetch + checkout + pull + restart`

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
sudo systemctl restart platform-api
sudo systemctl restart kpi-portal
```

解释：

- 服务器不直接做 `git reset` 这类破坏性回退
- 标准方式是先让本地仓库产生回滚提交，再让服务器同步该提交

如果服务器访问 GitHub 需要代理，则改用：

**服务器动作标签**：`谨慎做 / 回滚发布 / git fetch + pull with proxy + restart`

```bash
cd /opt/jenkins_robotframework
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 fetch origin
git checkout main
git -c http.proxy=http://10.144.1.10:8080 -c https.proxy=http://10.144.1.10:8080 pull --ff-only origin main
sudo systemctl restart platform-api
sudo systemctl restart kpi-portal
```

解释：

- 代理版回滚同步仍然遵循“本地先回滚提交，服务器再同步”的原则
- 服务器侧只负责拉取回滚后的目标版本并重启服务

**推荐发布标签**：

每次稳定发布后，在本地打标签：

```powershell
git tag -a release-2026-04-16 -m "stable release"
git push origin release-2026-04-16
```

**紧急临时回退**：

如果线上必须临时验证旧版本，可在服务器上临时切换到某个 tag 或 commit，但这不应作为标准长期流程，因为下次 `git pull` 会再次回到主线。

更规范的方式仍然是：

1. 在本地仓库回退或创建修复提交
2. push 到 GitHub
3. 服务器重新同步

---

## 故障排查

<a id="jenkins-troubleshooting-checklist"></a>

### Jenkins 排障清单

[返回故障现象快速入口](#quick-troubleshooting-entry)

适用场景：

- Jenkins 页面打不开
- Jenkins 登录跳转异常
- 改了 Prefix、override、Java 参数后怀疑没生效

按下面顺序排查：

```bash
sudo systemctl status jenkins
systemctl is-active jenkins
sudo journalctl -u jenkins -n 100
sudo ss -lntp | grep :8080
curl -I http://127.0.0.1:8080/
curl -I http://127.0.0.1:8080/login
curl -I http://127.0.0.1:8080/jenkins/
sudo systemctl show jenkins --property=Environment
sudo systemctl cat jenkins
```

如果你刚改过 Jenkins 的 `.service` 或 `override.conf`，再执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart jenkins
sudo systemctl status jenkins
```

最短记忆规则：

- 先看服务状态
- 再看日志
- 再看 8080
- 再看本机 curl
- 最后才查 Prefix / override

<a id="nginx-troubleshooting-checklist"></a>

### Nginx 排障清单

[返回故障现象快速入口](#quick-troubleshooting-entry)

适用场景：

- 浏览器连不上 Jenkins HTTPS 入口
- `https://10.71.210.104/jenkins/` 返回 `404`、`502` 或连接失败
- Jenkins 本机能通，但外部 HTTPS 不通

按下面顺序排查：

```bash
sudo systemctl status nginx
systemctl is-active nginx
sudo nginx -t
sudo ss -lntp | grep :80
sudo ss -lntp | grep :443
curl -k -I https://127.0.0.1/jenkins/
curl -k -L https://127.0.0.1/jenkins/
sudo ls -l /etc/nginx/sites-available
sudo ls -l /etc/nginx/sites-enabled
sudo journalctl -u nginx -n 100
```

如果你刚改过 Nginx 配置文件，再执行：

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status nginx
```

最短记忆规则：

- 先看服务状态
- 再看配置语法
- 再看 80 / 443 监听
- 再看本机 HTTPS
- 最后才看站点启用和日志

<a id="portal-troubleshooting-checklist"></a>

### Portal 排障清单

[返回故障现象快速入口](#quick-troubleshooting-entry)

适用场景：

- `/api/health` 不通
- `/kpi/health` 不通
- Portal 页面或 API 异常

按下面顺序排查：

```bash
sudo systemctl status platform-api
sudo systemctl status kpi-portal
systemctl is-active platform-api
systemctl is-active kpi-portal
sudo journalctl -u platform-api -n 100
sudo journalctl -u kpi-portal -n 100
sudo ss -lntp | grep :8000
sudo ss -lntp | grep :8001
curl --noproxy localhost http://127.0.0.1:8000/health
curl --noproxy localhost http://127.0.0.1:8001/health
```

如果你刚改过 Portal 的 `.service` 文件，再执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart platform-api
sudo systemctl restart kpi-portal
sudo systemctl status platform-api
sudo systemctl status kpi-portal
```

重点核对：

- `WorkingDirectory`
- `Environment="PATH=.../venv/bin"`
- `ExecStart`

### 问题 1：服务器上的代码和 GitHub 不一致

**原因**：有人直接在服务器修改了代码。  
**处理**：

1. 先备份服务器当前改动
2. 对比与 GitHub 的差异
3. 把有效改动回收到本地仓库
4. 重新提交 Git
5. 服务器恢复为仓库同步模式

### 问题 2：`git pull` 失败，提示本地有修改

**原因**：服务器工作区被手工改脏了。  
**处理原则**：

- 不要直接粗暴覆盖
- 先 `git status`
- 先确认这些变更是否应该进入 GitHub

### 问题 3：服务重启失败

检查：

**服务器动作标签**：`允许做 / 运维检查 / journalctl`

```bash
sudo journalctl -u platform-api -n 100
sudo journalctl -u kpi-portal -n 100
sudo journalctl -u jenkins -n 100
```

解释：

- `journalctl` 用于读取最近的服务日志
- 它属于排障检查动作，不会改动服务配置和业务源码

### 问题 4：依赖安装后仍然报模块缺失

通常是以下原因之一：

- 没有进入对应虚拟环境
- `requirements.txt` 未提交到 GitHub
- 服务器 `git pull` 后没有重新执行 `pip install -r requirements.txt`

### 问题 5：发布后访问到的仍是旧页面

检查顺序：

1. 服务器代码是否已经 `git pull` 到最新 commit
2. 服务是否已重启
3. Nginx 是否需要 reload
4. 浏览器是否缓存旧页面

### 问题 6：`git status` 提示 dubious ownership

**原因**：仓库目录或 `.git` 目录的实际所有者与当前执行 Git 命令的用户不一致，常见于使用 `sudo git clone` 后没有正确把仓库 ownership 切回日常操作用户。

**处理原则**：

1. 优先修正目录 ownership，例如：`sudo chown -R ute:ute /opt/jenkins_robotframework`
2. 再重新执行 `git status` 验证
3. 只有在确认这是必须保留的跨用户共享目录时，才执行 `git config --global --add safe.directory /opt/jenkins_robotframework`

---

## 最终结论

从本版本文档开始，`jenkins-kpi-platform`、`kpi-portal`、`platform-api` 的标准工作方式明确如下：

- **代码在本地 IDE 中开发**
- **代码统一 push 到 GitHub 仓库**：`https://github.com/stella555359/jenkins_robotframework`
- **服务器通过 GitHub 拉取代码实现同步**
- **版本控制、发布、回滚都以 Git 为准**

也就是说，Debian 服务器以后是部署目标机，不是日常写代码的地方。

这套方式更适合后续长期维护，因为它同时解决了：

- 版本可追踪
- 多次修改可回滚
- 本地开发效率高
- 服务器环境干净
- Jenkins 自动化发布可持续扩展