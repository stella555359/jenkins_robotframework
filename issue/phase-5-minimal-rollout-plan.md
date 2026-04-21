# 第五步最小可运行链路实施计划

## 日期
2026-04-16

## 背景
当前 Jenkins HTTPS、Nginx 反向代理、`/jenkins/` 子路径访问已经打通，Windows 浏览器可以正常登录 Jenkins。

接下来准备进入主文档中的“第五步：三块代码的开发与部署方式”，但在正式推进前，需要先明确：

- 第五步第一阶段先做哪一块最合适
- 三块代码当前的最小可落地骨架是什么
- 本轮 commit 之后，第一轮最推荐的实施顺序是什么

## 当前仓库现状确认

### 1. jenkins-kpi-platform

当前已经存在基础目录：

- `jcasc/`
- `jobs/`
- `pipelines/`
- `scripts/`
- `resources/`
- `templates/`
- `vars/`

结论：

这部分已经具备“先承载 Jenkins 配置、部署脚本和流水线骨架”的基础，但当前阶段不需要先把它做重。

### 2. platform-api

当前已经具备：

- `app/main.py`
- `app/api/v1/router.py`
- `requirements.txt`
- `tests/test_health.py`
- `pyproject.toml`

结论：

这部分已经具备最小服务骨架，适合作为第五步第一阶段的首个落地点。

### 3. kpi-portal

当前已经具备：

- `app/main.py`
- `app/api/v1/router.py`
- `requirements.txt`
- `tests/test_health.py`
- `pyproject.toml`

结论：

这部分也已具备最小服务骨架，但建议放在 platform-api 之后推进。

### 4. deploy/scripts/deploy_all.sh

当前仓库已经存在统一部署脚本：

- 拉取代码
- 创建 venv
- 安装依赖
- 重启 `platform-api`
- 重启 `kpi-portal`

结论：

仓库已经具备第一轮最小部署链路，不需要回头补基础设施后才能开始第五步。

## 当前判断

### 第五步第一阶段先做哪一块最合适

建议顺序：

1. `platform-api`
2. `kpi-portal`
3. `jenkins-kpi-platform`

理由：

- `platform-api` 当前依赖更轻，更适合先打通“代码 -> 服务 -> systemd -> Nginx 路径”的第一条最小链路
- `kpi-portal` 可以复用同一套落地模式，在第一条链路成功后再复制推进
- `jenkins-kpi-platform` 当前应优先承担配置和部署编排角色，而不是先做重功能

## 三块代码的最小可落地骨架

### 1. jenkins-kpi-platform

当前阶段最小目标：

- 保留 `jcasc/`
- 保留 `pipelines/`
- 保留 `scripts/`
- 至少维护一个部署脚本入口
- 暂时不优先扩展复杂 Job DSL 和重型 Jenkins 逻辑

### 2. platform-api

当前阶段最小目标：

- `app/main.py`
- `/health` 路由
- 基础配置对象
- 最小测试
- `requirements.txt`
- 可被 `uvicorn app.main:app` 启动
- 可被 systemd 拉起
- 可通过 `/api/health` 由 Nginx 转发访问

### 3. kpi-portal

当前阶段最小目标：

- `app/main.py`
- `/health` 路由
- 基础配置对象
- 最小测试
- `requirements.txt`
- 可被 `uvicorn app.main:app` 启动
- 可被 systemd 拉起
- 可通过 `/kpi/health` 由 Nginx 转发访问

## 第一轮最推荐的实施顺序

建议按下面顺序推进：

1. 先做一次 commit 和 push，把当前 Jenkins / Nginx 已打通后的状态固化为基线
2. 本地先只完善 `platform-api` 的最小可运行状态
3. 本地跑通 `platform-api` 的测试和健康检查
4. push 到 GitHub
5. 服务器 `git pull`，部署并拉起 `platform-api`
6. 验证：
   - `http://127.0.0.1:8000/health`
   - `https://10.71.210.104/api/health`
7. 这条链路稳定后，再用同样方法推进 `kpi-portal`
8. 两个 Portal 都稳定后，再回到 `jenkins-kpi-platform` 收口第一版部署脚本、Pipeline、JCasC

## 结论

当前状态已经适合正式进入“第五步：三块代码的开发与部署方式”。

最稳的推进方式不是三块一起铺开，而是：

1. 先 commit + push 固化基线
2. 先做 `platform-api`
3. 再做 `kpi-portal`
4. 最后收口 `jenkins-kpi-platform`

## 后续注意

- 服务器后续只做 `git pull`、依赖安装、service 管理，不再手改业务源码
- 第五步第一轮目标是“最小可运行链路”，不是一次性把三块都做完整
- 下一步应继续细化为“第五步第一轮实施动作清单”，按当前仓库现状拆成逐条可执行步骤

## 第五步第一轮实施动作清单

下面这份清单按“先固化基线，再打通 platform-api，再复制到 kpi-portal”的顺序编排。

### A. 先固化当前基线

#### 步骤 1：本地检查当前工作区

在本地仓库执行：

```powershell
cd C:\TA\jenkins_robotframework
git status
```

目标：

- 确认当前改动就是你准备作为第五步起点的内容
- 确认没有你不想带进去的临时文件

#### 步骤 2：提交并推送当前基线

```powershell
cd C:\TA\jenkins_robotframework
git add .
git commit -m "docs: finalize jenkins ingress and phase-5 starting baseline"
git push origin main
```

目标：

- 把“Jenkins / Nginx 已打通”的当前状态固化到 GitHub
- 后面第五步如果出问题，至少有一个清晰基线可回看

### B. 先在本地打通 platform-api

#### 步骤 3：先确认 platform-api 最小骨架完整

重点确认这些文件存在：

- `platform-api/app/main.py`
- `platform-api/app/api/v1/router.py`
- `platform-api/requirements.txt`
- `platform-api/tests/test_health.py`

目标：

- 不在这一步扩展复杂业务接口
- 只保证最小健康检查链路可运行

#### 步骤 4：本地安装依赖并执行最小测试

如果当前使用本机 Python，建议在本地执行：

```powershell
cd C:\TA\jenkins_robotframework\platform-api
C:\Users\stlin\Python313\python.exe -m pip install -r requirements.txt
C:\Users\stlin\Python313\python.exe -m pytest tests\test_health.py
```

目标：

- 先验证最小测试通过
- 先在本地发现缺依赖、导入路径、配置对象问题

#### 步骤 5：本地启动 platform-api

```powershell
cd C:\TA\jenkins_robotframework\platform-api
C:\Users\stlin\Python313\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端验证：

```powershell
curl http://127.0.0.1:8000/health
```

目标：

- 确认最小服务能在本地真正启动
- 确认 `/health` 返回正常

#### 步骤 6：如果本地通过，再提交 platform-api 当前最小版本

```powershell
cd C:\TA\jenkins_robotframework
git status
git add .
git commit -m "feat: validate minimal platform api health flow"
git push origin main
```

目标：

- 把第一条最小可运行链路的代码状态推到 GitHub

### C. 在服务器部署 platform-api

#### 步骤 7：服务器同步最新代码

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main
```

如果服务器访问 GitHub 需要代理，则改用文档里的代理版命令。

#### 步骤 8：在服务器安装 platform-api 依赖

```bash
cd /opt/jenkins_robotframework/platform-api
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

目标：

- 保证服务器运行环境和当前代码匹配

#### 步骤 9：确认或创建 platform-api.service

如果服务文件还没正式落地，按主文档中的 service 模板创建：

- `WorkingDirectory=/opt/jenkins_robotframework/platform-api`
- `Environment="PATH=/opt/jenkins_robotframework/platform-api/venv/bin"`
- `ExecStart=/opt/jenkins_robotframework/platform-api/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`

然后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl enable platform-api
sudo systemctl restart platform-api
sudo systemctl status platform-api
```

#### 步骤 10：先做服务器本机验证

```bash
curl --noproxy localhost http://127.0.0.1:8000/health
```

目标：

- 先确认后端本体在服务器上已经跑起来

#### 步骤 11：再做 Nginx 路径验证

```bash
curl -k -I https://10.71.210.104/api/health
curl -k https://10.71.210.104/api/health
```

目标：

- 确认 `/api/health` 已通过 Nginx 暴露成功

### D. 再复制到 kpi-portal

#### 步骤 12：按同样方法在本地验证 kpi-portal

```powershell
cd C:\TA\jenkins_robotframework\kpi-portal
C:\Users\stlin\Python313\python.exe -m pip install -r requirements.txt
C:\Users\stlin\Python313\python.exe -m pytest tests\test_health.py
C:\Users\stlin\Python313\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

另开终端验证：

```powershell
curl http://127.0.0.1:8001/health
```

#### 步骤 13：提交并推送 kpi-portal 当前最小版本

```powershell
cd C:\TA\jenkins_robotframework
git status
git add .
git commit -m "feat: validate minimal kpi portal health flow"
git push origin main
```

#### 步骤 14：服务器部署 kpi-portal

```bash
cd /opt/jenkins_robotframework
git fetch origin
git checkout main
git pull --ff-only origin main

cd /opt/jenkins_robotframework/kpi-portal
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

服务文件落地后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl enable kpi-portal
sudo systemctl restart kpi-portal
sudo systemctl status kpi-portal
```

#### 步骤 15：验证 kpi-portal

```bash
curl --noproxy localhost http://127.0.0.1:8001/health
curl -k -I https://10.71.210.104/kpi/health
curl -k https://10.71.210.104/kpi/health
```

### E. 第一轮完成标准

第一轮不追求复杂业务功能，只要满足下面这些条件，就算完成：

1. `platform-api` 本地测试通过
2. `platform-api` 本地 `/health` 可访问
3. 服务器本机 `http://127.0.0.1:8000/health` 可访问
4. 外部 `https://10.71.210.104/api/health` 可访问
5. `kpi-portal` 本地测试通过
6. `kpi-portal` 本地 `/health` 可访问
7. 服务器本机 `http://127.0.0.1:8001/health` 可访问
8. 外部 `https://10.71.210.104/kpi/health` 可访问

### F. 第一轮结束后再做什么

第一轮完成后，再进入下一阶段：

1. 补充 Portal 真实业务接口
2. 收口 `deploy/scripts/deploy_all.sh`
3. 把 Jenkins Pipeline 与部署脚本正式接起来
4. 再逐步完善 JCasC、Job DSL、自动化发布细节