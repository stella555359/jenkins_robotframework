# jenkins_robotframework

统一管理 Jenkins 自动化测试平台相关代码、部署模板和运行配置。

## 目录说明

- `jenkins-kpi-platform/`: Jenkins 配置、Pipeline、脚本
- `automation-portal/`: React 门户前端代码
- `reporting-portal/`: Reporting 服务代码
- `deploy/`: 部署脚本、systemd、nginx 模板
- `docs/`: 仓库内文档

## 当前部署约定

- 本地开发路径：`C:\TA\jenkins_robotframework`
- 服务器部署路径：`/opt/jenkins_robotframework`
- Master: `10.71.210.104`
- Agent: `10.57.159.149`
- SSH 用户：`ute`

## 标准发布流程

1. 本地开发并提交 Git。
2. Push 到 GitHub `main` 或目标分支。
3. 在服务器执行 `git pull --ff-only origin main`。
4. 执行 `deploy/scripts/deploy_all.sh`。
5. 验证 `reporting-portal` 健康检查和前端页面可访问性。