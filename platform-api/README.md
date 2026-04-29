# platform-api

`platform-api` 是当前轻量化自动化平台的 FastAPI 后端。

第一轮先从最小骨架开始，只打通：

- `GET /api/health`
- `POST /api/runs`
- `GET /api/runs`
- `GET /api/runs/{run_id}`

后续再逐步扩展：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- Jenkins handoff / callback contract
- 更完整的 SQLite 持久化

当前 `POST /api/runs` 已经会把最小 run 元数据写入 `SQLite`，默认数据库路径为：

- `data/results/automation_platform.db`

如需覆盖默认值，可在 `.env` 中设置：

- `RUNS_DB_PATH`

## Test Setup

当前测试已经引入两项基础测试工程能力：

- `pytest fixture`：统一放在 `tests/conftest.py`
- `allure-pytest`：用于输出 Allure 结果文件

服务器上执行普通 pytest：

```bash
cd /path/to/jenkins_robotframework/platform-api
python -m pytest tests
```

如果要产出 Allure 结果文件：

```bash
python -m pytest tests --alluredir=allure-results
```

注意：

- `allure-pytest` 只负责生成 `allure-results/`
- 如果要看 HTML 报告，还需要额外安装 Allure CLI，或在 Jenkins 中接 Allure 报告能力

如果服务器已安装 Allure CLI，可用：

```bash
allure serve allure-results
```

## API Testing Layers

当前 `platform-api` 这一阶段，建议先把测试分成 3 层来理解：

1. API 契约层

- 工具：`TestClient`
- 重点：状态码、响应结构、错误语义、字段是否齐全
- 示例：`GET /api/health`、`GET /api/runs/{run_id}`、`POST /api/runs`

2. 持久化验证层

- 工具：`db_connection` fixture
- 重点：接口动作之后，数据库里是否真的写入/查出预期记录
- 示例：创建 run 后检查 `runs` 表里的记录是否正确

3. 系统/集成层

- 工具：服务器执行、Jenkins、后续 Agent/Robot 链路
- 重点：真实环境中的依赖交互、状态回写、产物和端到端流程
- 当前阶段先不做重，只保留为后续扩展方向

当前最推荐的节奏是：

- 先用 API 契约层把接口行为测稳
- 再用少量持久化验证层确保不是“假接口”
- 等接 `jenkins-integration` 后，再逐步加系统测试层

当前边界说明：

- `platform-api` 负责 run contract、callback 和查询接口
- 通用 Jenkins job / pipeline / checkout / bridge 逻辑放在 `jenkins-integration/`
