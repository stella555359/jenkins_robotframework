# Step 9：`GET /api/runs/{run_id}` 详情接口

## 这一步的目标

把“按 `run_id` 精确查询单条 run 记录”这条链路打通。

当前需要明确两件事：

- 已知 `run_id` 时，能查到这条 run 的详情
- 查不到时，要明确返回 `404`

## 预期结果

这一轮做完后，系统应该具备下面这些可观察结果：

- `GET /api/runs/{run_id}`
- 按 `run_id` 从 `runs` 表查单条记录
- 查不到时稳定返回 `404`
- 列表接口里能看到的 run，可以按同一个 `run_id` 继续查详情

这一轮先不扩的内容包括：

- Jenkins 触发后的状态流转字段
- artifact / KPI 等详情扩展字段
- 复杂筛选、分页、聚合视图

## 这一步的代码设计

这一轮代码设计的核心，是把“按 ID 查单条记录”的语义和“查列表”明确区分开：

- `router`
  - 接收 path 参数 `run_id`
  - 暴露 `GET /api/runs/{run_id}`
- `service`
  - 决定“查到 / 查不到”这层业务语义
  - 查不到时抛 `404`
  - 查到时组装 `RunDetailResponse`
- `repository`
  - 只负责按 `run_id` 去 `runs` 表查单条记录
- `schema`
  - 用 `RunDetailResponse` 固定详情接口的第一版字段集合

这一轮真正新增的关键函数是：

```text
get_run() -> get_run_detail() -> get_run_record_by_id()
```

## 函数调用流程图

```mermaid
flowchart TD
Caller["调用方"] --> Router["router: get_run(run_id)"]
Router --> Service["service: get_run_detail(run_id)"]
Service --> Repo["repository: get_run_record_by_id(run_id)"]
Repo --> Db["SQLite: runs 表"]
Repo --> Service
Service -->|"命中"| Response["RunDetailResponse"]
Service -->|"未命中"| NotFound["HTTP 404"]
Response --> Json["JSON 响应"]
NotFound --> ErrorJson["{\"detail\": \"Run not found.\"}"]
```

## 开发侧验收步骤（服务器侧执行）

下面这组步骤用于确认“这轮代码功能已经在服务器上真实工作”，重点不是跑 pytest，而是手动走通功能链路。

### 1. 启动服务

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 2. 先创建一条 run，拿到真实 `run_id`

```bash
curl -X POST http://127.0.0.1:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"testline":"smoke","robotcase_path":"cases/login.robot"}'
```

预期先拿到类似这样的结果：

```json
{
  "run_id": "run-20260422104958123",
  "status": "created",
  "message": "Run request accepted."
}
```

### 3. 用上一步拿到的 `run_id` 查详情

把 `<run_id>` 替换成上一步创建出来的真实值：

```bash
curl http://127.0.0.1:8000/api/runs/<run_id>
```

### 4. 查一个不存在的 `run_id`

```bash
curl http://127.0.0.1:8000/api/runs/run-not-exists
```

### 5. 再查一次列表，确认同一个 `run_id` 能在列表和详情里对上

```bash
curl http://127.0.0.1:8000/api/runs
```

## 开发侧验收结果

- [x] `router.py` 已补上 `GET /api/runs/{run_id}` 路由，接口路径可访问
- [x] `run_service.py` 已能区分“查到返回详情”和“查不到抛 404”
- [x] `run_repository.py` 已补上按 `run_id` 查询单条记录的方法
- [x] 用真实创建出来的 `run_id` 可以查到单条详情
- [x] 不存在的 `run_id` 会稳定返回 `404`
- [x] 列表里能看到的 run，详情接口能按同一个 `run_id` 精确查到
- [x] 详情接口第一版字段已经和当前数据库主字段保持一致

## 测试侧验收步骤（服务器侧执行）

下面这组步骤用于确认自动化测试已经覆盖这轮主路径。

```bash
python -m pytest tests/test_health.py tests/test_runs.py
python -m pytest tests/test_health.py tests/test_runs.py --alluredir=allure-results
allure serve allure-results
```

如果服务器上暂时没有 `allure` CLI，也可以先完成前两步，至少确认 pytest 和 `allure-results` 产出正常。

这一轮测试侧重点关注：

- 命中路径：已有 `run_id` 时能否正确返回详情
- 未命中路径：不存在的 `run_id` 是否稳定返回 `404`
- 一致性：列表能看到的 run，详情能否按同一 `run_id` 查到
- 工程配套：fixture 和 Allure 基础接入是否正常工作

## 测试侧验收结果

- [x] pytest 已覆盖详情接口命中路径
- [x] pytest 已覆盖详情接口未命中路径
- [x] pytest 已覆盖列表接口与详情接口的一致性场景
- [x] pytest 已覆盖带后缀的 `run_id` 详情查询场景
- [x] `tests/conftest.py` 已收敛公共 fixture，减少重复准备逻辑
- [x] `allure-pytest` 已接入，测试结果可输出到 `allure-results`

## 当前最适合复盘的点

- 详情接口为什么不能用假数据顶替
- 为什么 `404` 比 `200 + {}` 更利于接口语义和测试判断
- fixture 和 Allure 在这个阶段分别解决了什么工程问题

## 相关专题与测试文档

- [Testing Workflow](../guides/testing-workflow.md)
- [API 设计与调用链](../guides/api-design-and-flow.md)
- [Step 9 测试设计训练](../testing-training/step-09-test-training.md)
- [Step 9 测试自动化](../testing-automation/step-09-test-automation.md)
