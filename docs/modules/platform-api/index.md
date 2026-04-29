# Platform API 学习总索引
## FastAPI 从零开始的分步实践

这份文档现在只承担 3 个职责：

1. 看当前做到哪一步
2. 快速跳转到某个 step
3. 快速跳转到稳定专题文档

也就是说，它不再承载所有细节解释，而是作为 `platform-api` 学习与复盘的总入口。

## Start Here / 先看这里

如果你是：

- 新开一个会话
- Cursor 刚重启
- 一时忘了当前项目文档该从哪里看起

先按下面顺序恢复上下文：

1. 先看这份索引页的：
   - `当前进度看板`
   - `最近 4 个 step`
2. 再看稳定专题：
   - [Testing Workflow](guides/testing-workflow.md)
   - [API 设计与调用链](guides/api-design-and-flow.md)
3. 再进入当前正在推进的 step 文档
4. 如果当前 step 已经开始做测试自动化，再补看：
   - `docs/modules/platform-api/testing-automation/`
   - `docs/modules/platform-api/testing-training/`

最短恢复路径：

```text
先看索引 -> 再看专题 -> 再看当前 step -> 最后看对应 testing 文档
```

## 怎么使用这份索引

- 想看当前进度：先看“进度看板”
- 想复盘某一步：去 `docs/modules/platform-api/steps/`
- 想回看稳定知识：去 `docs/modules/platform-api/guides/`

## 当前专题文档

- [Testing Workflow](guides/testing-workflow.md)
- [API 设计与调用链](guides/api-design-and-flow.md)

系统级架构另见：

- `docs/overview/gnb-kpi-regression-architecture.md`
- `docs/overview/gnb-kpi-system-runtime.md`

## 当前进度看板

- [x] Step 1：补最小目录结构
- [x] Step 2：实现 `GET /api/health`
- [x] Step 3：加入基础配置层
- [x] Step 4：加入 run 相关 schema
- [x] Step 5：实现 `POST /api/runs`
- [x] Step 6：确定 `POST /api/runs` 第一版最小返回语义
- [x] Step 7：接入 SQLite，让 `POST /api/runs` 真正创建 run 记录
- [x] Step 8：实现 `GET /api/runs`
- [x] Step 9：实现 `GET /api/runs/{run_id}`
- [ ] Step 10：冻结 executor-agnostic run contract
- [ ] Step 11：冻结 Jenkins handoff / callback 最小闭环
- [ ] Step 12：补齐 artifact / KPI / detector metadata 查询面
- [ ] Step 13：把 run detail 升级为 execution-ready 详情入口

## 最近 4 个 step

- [Step 6：`POST /api/runs` 第一版返回语义](steps/step-06-run-create-response-semantics.md)
- [Step 7：`POST /api/runs` + SQLite 最小闭环](steps/step-07-post-runs-and-sqlite.md)
- [Step 8：`GET /api/runs` 列表接口](steps/step-08-get-runs-list.md)
- [Step 9：`GET /api/runs/{run_id}` 详情接口](steps/step-09-get-run-detail.md)

## 当前规划中的后续 4 个 step

- [Step 10：冻结 executor-agnostic run contract](steps/step-10-executor-agnostic-run-contract.md)
- [Step 11：冻结 Jenkins handoff / callback 最小闭环](steps/step-11-jenkins-trigger-and-callback.md)
- [Step 12：补齐 artifact / KPI / detector metadata 查询面](steps/step-12-artifact-and-kpi-metadata-query-surface.md)
- [Step 13：把 run detail 升级为 execution-ready 详情入口](steps/step-13-execution-ready-run-detail.md)

## 早期步骤简表

- Step 0：建立 `platform-api` 过程记录文档
- Step 1：补最小目录结构，并写 `GET /api/health`
- Step 2：理解 `GET /api/health` 请求链路
- Step 3：理解 schema 的两种角色
- Step 4：确定 `POST /api/runs` 第一版最小请求体
- Step 5：为 `POST /api/runs` 设计第一版输入 / 输出字段

## 当前最值得优先看的内容

如果你现在只想抓住关键知识，优先看：

1. [Testing Workflow](guides/testing-workflow.md)
2. [API 设计与调用链](guides/api-design-and-flow.md)
3. [Step 10：executor-agnostic run contract](steps/step-10-executor-agnostic-run-contract.md)
4. [Step 11：Jenkins handoff / callback](steps/step-11-jenkins-trigger-and-callback.md)
5. [Step 12：artifact / KPI metadata](steps/step-12-artifact-and-kpi-metadata-query-surface.md)

## 当前协作约定

- 每个新 step 优先写进独立 step 文件
- 稳定知识优先沉淀进专题文档
- 本索引页只保留进度、入口和极简摘要
- step 文档统一按模块 README 里定义的标准模板编写
- 从当前开始，`platform-api` 继续按 `backend-first` 主线往下推进

## 说明

这次重构先做“最小可读版本”：

- 最近 4 个 step 已拆出
- 测试工作流和 API 设计已抽成专题
- 下方历史内联内容先保留为过渡区，后续如有需要再继续拆分

---

## 历史内联内容（过渡保留区）

下面保留的是重构前已经写在本文件里的历史内容。

现在如果你只是想快速复盘，优先使用上面的：

- 总索引
- 独立 step 文档
- 专题指南

只有在你明确想回看旧版原始记录时，再往下翻。

---

## Step 0：开始前说明

### 这一步要解决什么问题

先建立一份专门的过程记录文档，把后续 `platform-api` 的实现步骤单独沉淀下来。

### 这一步做了什么

- 创建了 `docs/modules/platform-api/index.md`
- 确定后续统一按“小步实现 + 小步验证 + 小步解释”的方式推进

### 当前状态

- `platform-api` 目录目前还是很薄的占位状态
- 还没有开始写真正的 FastAPI 入口代码
- 下一步将从最小目录结构和 `GET /api/health` 开始

### 验收结果

满足以下条件就算通过：

1. 过程记录文档已创建
2. 后续每一步都有地方持续追加
3. 当前下一步目标已经明确

---

## Step 1：补最小目录结构，并写 `GET /api/health`

### 这一步要解决什么问题

先把 `platform-api` 从“只有占位目录”变成“真正能承载 FastAPI 代码”的最小后端骨架。

这一轮不做 run、数据库、Jenkins 集成，只解决两个最基础的问题：

1. 代码该放在哪里
2. 服务起来之后，外部怎么判断它活着

### 这一步做了什么

- 新增 `app/` 应用目录，按 `api / core / schemas / services` 分层
- 新增 FastAPI 入口 `app/main.py`
- 新增配置层 `app/core/config.py`
- 新增健康检查 schema `app/schemas/health.py`
- 新增健康检查 service `app/services/health_service.py`
- 新增路由 `GET /api/health`
- 新增 `requirements.txt` 和最小测试文件

### 这一小步建议你先理解的目录结构

```text
platform-api/
  app/
    api/
      v1/
        router.py
    core/
      config.py
    schemas/
      health.py
    services/
      health_service.py
    main.py
  tests/
    test_health.py
  requirements.txt
```

这一步你只需要先理解每层职责：

- `main.py`：FastAPI 应用入口
- `router.py`：路由入口，定义接口地址
- `config.py`：配置读取
- `schemas/`：接口输入输出的数据结构
- `services/`：真正业务逻辑
- `tests/`：最小测试

### 代码示例 1：`requirements.txt`

```txt
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.8.0
pydantic-settings>=2.3.0
pytest>=8.0.0
```

### 逐行解释

1. `fastapi`：后端框架本体，用来写 API。
2. `uvicorn[standard]`：启动 FastAPI 服务的 ASGI 服务器。
3. `pydantic`：定义和校验数据结构。
4. `pydantic-settings`：专门负责从 `.env` 读取配置。
5. `pytest`：后面做最小测试用。

### 代码示例 2：`app/main.py`

```python
from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(api_router, prefix="/api")
```

### 逐行解释

1. `from fastapi import FastAPI`
   这一行是把 FastAPI 这个框架类导入进来。
2. `from app.api.v1.router import router as api_router`
   把路由对象导入进来，并给它一个更清楚的名字 `api_router`。
3. `from app.core.config import settings`
   把配置对象导入进来，后面应用名等信息从这里读取。
4. `app = FastAPI(...)`
   真正创建 FastAPI 应用实例。
5. `title=settings.app_name`
   Swagger 文档标题会显示成配置里的应用名。
6. `version="0.1.0"`
   先给一个最小版本号，方便后续迭代。
7. `app.include_router(api_router, prefix="/api")`
   把路由挂到应用上，并统一加上 `/api` 前缀，所以后面健康检查完整路径会变成 `/api/health`。

### 代码示例 3：`app/core/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Platform API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
```

### 逐行解释

1. `BaseSettings`
   这是 Pydantic 提供的配置基类，专门用来读环境变量。
2. `SettingsConfigDict`
   用来声明配置文件读取规则。
3. `class Settings(BaseSettings):`
   定义一个配置类，后面项目配置统一从这里取。
4. `app_name`
   应用名称，默认是 `Platform API`。
5. `app_env`
   当前环境，默认先用 `development`。
6. `app_host`
   服务监听地址。
7. `app_port`
   服务监听端口。
8. `model_config = SettingsConfigDict(...)`
   告诉 Pydantic：可以从 `.env` 文件读取配置。
9. `extra="ignore"`
   `.env` 里即使有暂时没定义的配置项，也先忽略，不报错。
10. `settings = Settings()`
    实例化一个全局配置对象，别的文件导入它就能直接使用。

### 代码示例 4：`app/schemas/health.py`

```python
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
```

### 逐行解释

1. `BaseModel`
   Pydantic 的基础模型类，用来定义接口返回的数据结构。
2. `class HealthResponse(BaseModel):`
   定义健康检查接口的返回格式。
3. `status`
   服务状态，例如 `ok`。
4. `service`
   服务名称。
5. `environment`
   当前运行环境。

### 代码示例 5：`app/services/health_service.py`

```python
from app.core.config import settings


def get_health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }
```

### 逐行解释

1. 导入 `settings`
   因为返回值里想带上服务名和环境信息。
2. `def get_health_payload()`
   单独放一个 service 函数，表示“真正返回什么内容”属于业务逻辑，而不是路由层逻辑。
3. `-> dict[str, str]`
   表示这个函数返回的是字符串字典。
4. `"status": "ok"`
   健康检查最核心的状态。
5. `"service": settings.app_name`
   返回当前服务名。
6. `"environment": settings.app_env`
   返回当前环境。

### 代码示例 6：`app/api/v1/router.py`

```python
from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import get_health_payload

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def get_health() -> HealthResponse:
    return HealthResponse(**get_health_payload())
```

### 逐行解释

1. `APIRouter`
   FastAPI 用它来组织一组接口。
2. 导入 `HealthResponse`
   用于声明这个接口应该返回什么格式。
3. 导入 `get_health_payload`
   业务数据从 service 层拿，不直接写死在路由函数里。
4. `router = APIRouter()`
   创建一个路由对象。
5. `@router.get("/health", ...)`
   定义一个 GET 接口，路径是 `/health`。
6. `response_model=HealthResponse`
   告诉 FastAPI：返回值要按 `HealthResponse` 这个结构校验并生成文档。
7. `tags=["health"]`
   Swagger 里会把这个接口归到 `health` 分组。
8. `def get_health()`
   路由处理函数。
9. `return HealthResponse(**get_health_payload())`
   先从 service 拿到字典，再转成 schema 对象返回。

### 代码示例 7：`tests/test_health.py`

```python
from app.services.health_service import get_health_payload


def test_health_payload_contains_expected_fields() -> None:
    payload = get_health_payload()

    assert payload["status"] == "ok"
    assert payload["service"] == "Platform API"
    assert "environment" in payload
```

### 逐行解释

1. 这里只先测 service，不急着上接口级测试。
2. `payload = get_health_payload()`
   先拿到健康检查数据。
3. `assert payload["status"] == "ok"`
   确认状态对不对。
4. `assert payload["service"] == "Platform API"`
   确认服务名默认值对不对。
5. `assert "environment" in payload`
   确认环境字段存在。

### 你自己动手时的落代码顺序

建议你不要一口气全写，按下面顺序自己落：

1. 先建目录：`app/api/v1`、`app/core`、`app/schemas`、`app/services`、`tests`
2. 再写 `requirements.txt`
3. 再写 `config.py`
4. 再写 `health.py`
5. 再写 `health_service.py`
6. 再写 `router.py`
7. 最后写 `main.py`

这样做的原因是：`main.py` 依赖前面几个文件，放最后写最不容易乱。

### 相关问题记录

这一节用于沉淀在当前 step 里出现的追问。后面如果你对这一小步还有新的问题，也继续补在这里。

#### 问题 1：`get_health_payload() -> dict[str, str]` 里的 `-> dict[str, str]` 是什么意思？

这是 Python 的**返回值类型标注**。

它的意思是：这个函数返回的是一个 `dict`，并且：

- key 是 `str`
- value 也是 `str`

所以这句：

```python
def get_health_payload() -> dict[str, str]:
```

可以先理解成：

“`get_health_payload()` 这个函数，最后会返回一个 `字符串: 字符串` 的字典。”

对应到当前这个函数，返回值大概就是：

```python
{
    "status": "ok",
    "service": "Platform API",
    "environment": "development",
}
```

这里三组 key 和 value 都是字符串，所以写成 `dict[str, str]` 是合理的。

这个标注不是运行必须的，但它有三个常见作用：

1. 让人一眼看懂函数准备返回什么
2. 让 IDE 更容易做提示和检查
3. 后面代码复杂之后，更不容易把返回值写乱

你可以把它先记成：**给函数返回值写了一张说明书**。

#### 问题 2：`health_service` 是干嘛的？健康检查的作用是什么？

`health_service` 可以先理解成：

**专门负责“健康检查这件小事”的业务逻辑层。**

在当前最小项目里，它做的事情很简单，就是统一返回一份健康状态数据，例如：

- 服务是不是活着
- 服务名是什么
- 当前环境是什么

而 `router.py` 的职责不是组织这些数据，而是：

- 暴露接口地址
- 接收 HTTP 请求
- 调用 service
- 把结果返回给调用方

也就是说：

- `router.py`：负责接请求
- `health_service.py`：负责真正准备返回数据

健康检查接口本身的作用，核心就是：

**快速判断这个服务现在是不是正常活着。**

它的常见用途包括：

1. 启动后自检  
   服务起来之后，先访问 `/api/health`，确认它至少已经能响应请求。
2. 排查问题  
   如果后面页面打不开、Jenkins 回调失败、Nginx 代理异常，先看 `/api/health` 通不通，就能快速判断是不是 FastAPI 根本没起来。
3. 联调第一站  
   在复杂业务接口还没开始做之前，`/api/health` 是最好验证的一条链路。
4. 部署验收  
   后面服务部署到 Jenkins Master 或目标服务器后，最先验证的通常也是这个接口。

如果用一句很口语的话概括：

- `health_service` = 准备“我还活着”这份数据的人
- `/api/health` = 对外汇报“我还活着”的窗口

#### 问题 3：为什么现在要分成 `main.py`、`router.py`、`health_service.py` 这三层？

不是因为 `health` 这个功能有多复杂，而是因为你现在就在给后面更复杂的接口打基础。

最简单理解：

- `main.py`：管“把整个 FastAPI 应用启动起来”
- `router.py`：管“接口地址长什么样、请求进来先到哪”
- `health_service.py`：管“这个接口到底返回什么数据”

可以先把这三层记成一句话：

**`main` 负责组装，`router` 负责接请求，`service` 负责干活。**

为什么不现在全写在一个文件里？

因为现在虽然只有健康检查，写在一起也能跑；但后面你一旦开始做：

- `POST /api/runs`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- Jenkins 回调
- SQLite 持久化

如果还全堆在一个文件里，就会很快变乱。

现在先拆开，后面每加一个功能都还能保持清楚。

你可以把当前这条最小链路记成下面这个小流程图：

```text
浏览器 / curl
   |
   v
GET /api/health
   |
   v
router.py
   |   识别这是哪个接口
   v
health_service.py
   |   准备返回数据
   v
router.py
   |   包装成 HealthResponse
   v
返回 JSON 给调用方
```

如果想再压缩成最容易记住的版本，就是：

```text
入口 main -> 路由 router -> 逻辑 service -> 返回结果
```

#### 问题 4：服务器上调试时要不要建 `.venv`？是每个模块一个，还是整个仓库共用一个？

建议是：

**每个 Python 模块一个 `.venv`，不要整个 `jenkins_robotframework` 仓库共用一个。**

先说这次的 `platform-api`：

- 推荐在 `platform-api/` 目录下建自己的 `.venv`
- 后面启动、测试、部署都尽量使用这个环境里的 `python`

为什么推荐“每个模块一个”：

1. 依赖隔离更清楚  
   `platform-api` 后面会有自己的 FastAPI、Pydantic、数据库相关依赖；别的 Python 模块未必完全一样。
2. 降低冲突  
   如果整个仓库共用一个 `venv`，一个模块升级依赖，可能把另一个模块带崩。
3. 部署更贴近真实运行方式  
   以后 `platform-api` 如果是独立服务，它本来就应该有自己独立的运行环境。
4. 排查问题更简单  
   出问题时更容易判断：这是 `platform-api` 自己的依赖问题，不是仓库里别的模块带出来的。

对你这个仓库，推荐先这样理解：

- `platform-api`：单独一个 `.venv`
- `automation-portal`：它不是 Python 项目，不用 `venv`，它用的是 `node_modules`
- 如果后面还有独立 Python 工具模块，例如单独部署的脚本服务，也建议它们各自有自己的 `.venv`

推荐的目录理解方式：

```text
jenkins_robotframework/
  platform-api/
    .venv/
  automation-portal/
    node_modules/
```

不要一开始就在仓库根目录建一个通用 `.venv` 让所有模块混着用。

### 涉及文件

- `platform-api/requirements.txt`
- `platform-api/README.md`
- `platform-api/app/main.py`
- `platform-api/app/api/v1/router.py`
- `platform-api/app/core/config.py`
- `platform-api/app/schemas/health.py`
- `platform-api/app/services/health_service.py`
- `platform-api/tests/test_health.py`

### 如何验证

这一步的验证，默认优先在 Jenkins Master 或目标服务器上做。

这里默认假设 Jenkins Master / 目标服务器是 Linux 环境，所以命令使用 `python3` 和 `source`。

#### 方式 A：推荐做法（服务器 / Jenkins Master 验证）

先把代码同步到服务器对应目录，然后执行：

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests/test_health.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端窗口验证：

```bash
curl http://127.0.0.1:8000/api/health
```

#### 方式 B：可选做法（本地验证）

只有在你本机恰好已经具备 Python 环境时，才做本地验证：

```powershell
cd C:\TA\jenkins_robotframework\platform-api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests/test_health.py
python -m uvicorn app.main:app --reload
curl http://127.0.0.1:8000/api/health
```

期望返回类似：

```json
{"status":"ok","service":"Platform API","environment":"development"}
```

### 验收结果

- [x] `platform-api` 已经不再只是空目录，最小代码骨架已补齐
- [x] 已经存在明确的 `GET /api/health` 路由
- [x] 代码语法已通过本地编译检查
- [ ] Jenkins Master / 服务器上 `pytest` 通过
- [ ] Jenkins Master / 服务器上实际访问 `http://127.0.0.1:8000/api/health` 成功
- [ ] 如本机具备环境，可选补充本地验证

### 我这一步学到了什么

- FastAPI 最开始不用追求“大而全”，先把入口、路由、schema、service 分开就够了
- 健康检查接口虽然简单，但它是后面接 Nginx、systemd、Jenkins 回调时最基础的验证点

---

## Step 2：理解 `GET /api/health` 请求链路（对应进度看板第 2 步）

### 这一步要解决什么问题

Step 1 更偏向“代码骨架先有了”，但你还需要真正理解：

当浏览器或 `curl` 去访问 `GET /api/health` 时，请求到底是怎么一步一步走到返回结果的。

这一小步不新增新功能，重点是把**请求链路**在脑子里串起来。

### 代码示例

先把这几个关键文件连起来看：

```python
# app/main.py
from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")
app.include_router(api_router, prefix="/api")

# app/api/v1/router.py
from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.health_service import get_health_payload

router = APIRouter()

@router.get("/health", response_model=HealthResponse, tags=["health"])
def get_health() -> HealthResponse:
    return HealthResponse(**get_health_payload())

# app/services/health_service.py
from app.core.config import settings

def get_health_payload() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
    }

# app/schemas/health.py
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
```

### 函数调用流程图（含大概意思）

这一步不再按代码逐行拆，而是先把“谁调用谁、每层大概干什么”看明白。

```text
浏览器 / curl
   |
   | 访问 GET /api/health
   v
FastAPI app（main.py）
   |
   | 负责接住请求；app 是在 main.py 里创建出来的
   v
router.py -> get_health()
   |
   | 负责找到这个接口对应的处理函数
   v
health_service.py -> get_health_payload()
   |
   | 负责准备原始业务数据
   v
HealthResponse schema
   |
   | 负责约束返回结构和字段类型
   v
FastAPI JSON response
   |
   | 负责把结果序列化成最终 JSON
   v
返回给调用方
```

最短记忆版：

```text
请求进来 -> app 分发 -> router 接口函数 -> service 准备数据 -> schema 约束结构 -> FastAPI 返回 JSON
```

### 这一条链路怎么记最方便

推荐你用下面这条简化版记忆：

```text
请求进来
-> main.py 里的应用接住
-> router.py 找到对应接口
-> health_service.py 准备数据
-> schema 校验/包装
-> FastAPI 返回 JSON
```

如果你想记成更短的一句，可以直接记：

```text
main 负责接应用，router 负责接请求，service 负责准备数据，schema 负责约束返回结构
```

### 小流程图

```text
浏览器 / curl
   |
   v
GET /api/health
   |
   v
FastAPI app (main.py)
   |
   v
router.py -> get_health()
   |
   v
health_service.py -> get_health_payload()
   |
   v
HealthResponse
   |
   v
JSON 响应
```

### 更形象一点的流程图

```mermaid
flowchart LR
   A["浏览器 / curl<br/>访问 GET /api/health"]
   B["FastAPI app<br/>main.py"]
   C["api_router 已注册<br/>prefix=/api"]
   D["router.py<br/>get_health()"]
   E["health_service.py<br/>get_health_payload()"]
   F["返回原始字典<br/>status / service / environment"]
   G["HealthResponse<br/>做结构校验和包装"]
   H["FastAPI 自动转成 JSON"]
   I["调用方收到响应<br/>status=ok 等字段"]

   A --> B
   B --> C
   C --> D
   D --> E
   E --> F
   F --> G
   G --> H
   H --> I
```

你可以把这张图记成一句话：

```text
请求先进入 main.py 创建出来的 app，
app 再把 /api/health 分发给 router，
router 去调用 service 拿数据，
最后再交给 schema 包装后返回 JSON。
```

再补一个最短记忆点：

```text
main.py 里给整个 router 加了 prefix="/api"
router.py 里当前接口自己定义的是 "/health"
两段拼起来就是 "/api/health"
```

### 相关问题整理

这一节把前面零散追问过的问题，按更容易学习的顺序整理成 4 组：

1. 先理解请求是怎么进来的
2. 再理解结果是怎么返回出去的
3. 再理解 `GET` 和 `POST` 的区别
4. 最后理解为什么现在就要分 `router / service / schemas`

#### 1. 请求先到哪里？为什么最后地址是 `/api/health`？

可以这样理解：

- 请求先进入 FastAPI 应用
- FastAPI 应用是由 `main.py` 创建出来的
- 然后应用再根据已注册的路由，把请求分发到 `router.py`

所以更准确地说：

**先进入 `main.py` 创建出来的 app，再由 app 分发到 `router.py`。**

而最终访问地址为什么是 `/api/health`，原因在这里：

```python
app.include_router(api_router, prefix="/api")
```

这里统一给整个路由对象加了一个前缀 `/api`。

所以：

- 路由文件里定义的是 `"/health"`
- 最终对外暴露的是 `"/api/health"`

你可以把它压缩成最短记忆：

```text
main.py 里给整个 router 加了 prefix="/api"
router.py 里当前接口自己定义的是 "/health"
两段拼起来就是 "/api/health"
```

#### 2. `schema` 在这里起什么作用？返回给调用方的 JSON 是怎么来的？

这里可以分两层理解。

第一层：为什么有 `schema`

即使现在返回的数据很简单，`schema` 也能先帮你建立一个好习惯：

- 明确接口返回结构
- 避免字段名写乱
- 方便 Swagger 自动生成接口文档

现在你可能觉得“直接 return 字典也能跑”，这没错；但后面接口一多，`schema` 的价值会越来越明显。

第二层：JSON 是怎么真正返回给调用方的

- `service` 先准备原始字典
- `router` 用 `HealthResponse(**get_health_payload())` 把字典包装成 schema 对象
- 路由函数 `return` 的其实不是 JSON 字符串，而是一个 Python 对象
- 这个对象会先返回给 FastAPI 框架本身
- FastAPI 再自动把它序列化成 JSON 响应
- 最后通过 HTTP 返回给浏览器或 `curl`

也就是说，这一步不是你手工去写：

```python
return '{"status": "ok"}'
```

而是：

1. 你返回 `HealthResponse` 对象
2. FastAPI 负责检查字段结构是不是符合 schema
3. FastAPI 自动把这个对象转成 JSON
4. 调用方最终收到 HTTP 响应里的 JSON 内容

可以把这条链路记成一句话：

```text
service 产出数据 -> schema 把数据变规范 -> FastAPI 自动转成 JSON -> 通过 HTTP 响应发回调用方
```

#### 3. `POST` 请求和 `GET` 请求相比，主要多了哪一步？

最主要多出来的一步是：

**先接收并解析请求体里的输入数据，再按输入 schema 做校验。**

你可以先这样对比：

`GET /api/health` 更像：

```text
客户端来问一个问题 -> 后端准备结果 -> 返回结果
```

而 `POST /api/runs` 更像：

```text
客户端先交一张表 -> 后端先检查这张表填得对不对 -> 再继续处理 -> 最后返回结果
```

所以 `POST` 比 `GET` 多出来的关键动作就是：

```text
FastAPI 先解析请求体 body，并按输入 schema 校验字段和类型。
```

如果压缩成最短链路，可以记成：

```text
GET: 请求进来 -> router -> service -> 输出 schema -> JSON
POST: 请求进来 -> 解析 body -> 输入 schema 校验 -> router -> service -> 输出 schema -> JSON
```

#### 4. 为什么要分 `router`、`service`、`schemas`？如果只剩 `router` 会怎样？

可以先把三层职责记成一句话：

```text
router 负责接请求，service 负责干活，schemas 负责给输入输出立规矩。
```

它们分别管什么：

- `router`：接口地址、请求分发、调用哪段逻辑
- `service`：真正的业务处理，例如组织返回数据、保存 run、调用 Jenkins
- `schemas`：定义输入输出应该长什么样，字段名、类型、是否缺失都在这里约束

拿当前健康检查举例：

- `router.py` 里只关心：`GET /health` 该由 `get_health()` 处理
- `health_service.py` 里只关心：我要返回 `status / service / environment`
- `HealthResponse` 只关心：这三个字段都应该是字符串

例如：

```python
class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str
```

它其实是在给返回值立规矩：

- 必须有 `status`
- 必须有 `service`
- 必须有 `environment`
- 这三个字段都应该是 `str`

如果将来你误写成：

```python
{
    "status": "ok",
    "service_name": "Platform API"
}
```

那就会出现两个问题：

- 字段名写错了，`service` 变成了 `service_name`
- `environment` 还丢了

而用了 schema 后，这类问题会更早暴露出来。

如果没有 `service` 和 `schemas`，所有东西都堆在 `router` 里，最常见的不良结果是：

1. 路由函数会越来越胖  
   一个函数里既管请求参数、又管业务逻辑、又管返回格式，后面很难看懂。
2. 重复逻辑越来越多  
   多个接口如果都要拼相似数据、做相似校验，容易在不同路由里复制粘贴。
3. 返回格式容易漂移  
   今天字段叫 `service`，明天有人改成 `service_name`，没有统一约束就容易乱。
4. 测试更难写  
   如果所有逻辑都埋在 router 里，就不容易单独测业务函数。
5. 后续扩展更痛苦  
   现在只是 `health`，后面一旦加 `POST /api/runs`、数据库、Jenkins 回调，单文件会很快失控。

所以现在即使健康检查很简单，也先拆成这三层，是为了给后面的复杂接口留出清晰结构。

#### 问题 5：我目前对这条链路的理解是否正确？

你当时的原始理解是：

```text
FASTAPI main 接收到 url 请求，分发到相应的 router，
router 再根据 @router.get("/health") 对应到 service 的 get_health_payload，
再由 schemas 的 HealthResponse 检查数据类型返回结果给 router，
再由 FastAPI 处理成最终的 json 数据。
```

这个理解已经基本对了，主链路抓得很准，只需要做几个小修正：

1. 不是 `main.py` 本身直接接收请求  
   更准确地说，是 **`main.py` 创建出来的 FastAPI app** 接收请求。
2. `@router.get("/health")` 不是直接对应到 `service`  
   它先对应到路由函数 `get_health()`，然后 `get_health()` 再去调用 `service`。
3. `HealthResponse` 不是“把结果返回给 router”  
   更准确地说，它负责**约束返回结构、校验字段类型**，然后再由 FastAPI 把结果序列化成 JSON。

整理后的修正版可以这样记：

```text
FastAPI app 接收到对 /api/health 的请求后，
根据已注册的路由把请求分发到 router.py 里的 get_health()；
get_health() 再调用 service 层的 get_health_payload() 取得原始数据；
然后用 schemas 里的 HealthResponse 对返回结构做约束和校验；
最后 FastAPI 再把这个结果序列化成 JSON 返回给调用方。
```

如果想压缩成最短记忆版，可以直接记：

```text
请求 -> FastAPI app -> router函数 -> service取数据 -> schema约束结构 -> FastAPI转成JSON -> 返回
```

#### 问题 6：为什么先做 `GET /api/health`，不一上来就做 `POST /api/runs`？

你当时的直觉是：

```text
因为 GET 比 POST 步骤少，POST 看起来过程会更多一些。
```

这个方向是对的，而且已经抓住了最核心的一点：

**`GET /api/health` 比 `POST /api/runs` 更适合先做，是因为它链路更短、变量更少、排错更容易。**

可以再稍微展开成更完整一点的理解：

`GET /api/health` 这条链路通常只需要先确认：

- 路由通不通
- service 能不能返回数据
- schema 能不能正常输出
- FastAPI 能不能把结果转成 JSON

但如果一上来就做 `POST /api/runs`，通常会一下子多出很多新问题：

- 请求体 `body` 怎么传
- 输入 schema 怎么定义
- 字段校验怎么做
- 参数缺失怎么办
- 数据要不要落库
- 是否要生成 `run_id`
- 返回值结构怎么设计
- 后面是否要接 Jenkins

也就是说，`POST` 不只是“请求方法变了”，而是会多出一整层**输入处理和业务状态管理**。

所以更准确的一句话是：

**不是因为 GET 天生简单，而是因为 `health` 这个 GET 接口是最小闭环；而 `POST /api/runs` 会一下子引入请求体、校验、状态、持久化这些新复杂度。**

如果想压缩成最短记忆版，可以这样记：

```text
GET /api/health = 先验证“服务活着、路由通了、返回通了”
POST /api/runs = 除了路由和返回，还要处理“用户提交了什么、是否合法、要不要保存、返回什么状态”
```

### 涉及文件

- `platform-api/app/main.py`
- `platform-api/app/api/v1/router.py`
- `platform-api/app/services/health_service.py`
- `platform-api/app/schemas/health.py`

### 你自己动手时的落代码顺序

这一步主要是理解，不是新增文件。

建议你自己做下面这几个动作：

1. 打开 `main.py`，先只看 `include_router(...)` 这一句
2. 再打开 `router.py`，确认 `@router.get("/health")` 对应的是哪个函数
3. 再打开 `health_service.py`，确认最终返回的原始数据长什么样
4. 最后打开 `health.py`，看 schema 是怎么约束返回结果的
5. 自己尝试口述一遍这条调用链

### 如何验证

这一步的验证，重点不是“再写新代码”，而是确认你已经把调用链看明白了。

这里默认假设 Jenkins Master / 目标服务器是 Linux 环境，所以命令使用 `python3` 和 `source`。

#### 方式 A：推荐做法（Jenkins Master / 目标服务器验证）

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

再访问：

```bash
curl http://127.0.0.1:8000/api/health
```

如果访问成功，再去对照源码，回答下面三个问题：

1. 为什么访问地址是 `/api/health`，不是 `/health`
2. 是谁负责真正准备返回字典
3. `HealthResponse` 在这条链路里起什么作用

#### 方式 B：可选做法（本地验证）

如果你本机也具备 Python 环境，可以同样执行：

```powershell
cd C:\TA\jenkins_robotframework\platform-api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
curl http://127.0.0.1:8000/api/health
```

### 验收结果

- [ ] 你能自己说清楚 `/api/health` 这条请求链路
- [ ] 你能区分 `main.py`、`router.py`、`health_service.py`、`schema` 各自职责
- [ ] Jenkins Master / 服务器上能够访问 `http://127.0.0.1:8000/api/health`

### 我这一步学到了什么

- 一个接口真正跑起来，不只是“写个函数”，而是请求分发、业务处理、数据约束一起配合
- 现在先把健康检查链路看懂，后面再做 `POST /api/runs` 会容易很多

---

## Step 3：理解 schema 的两种角色（为 `POST /api/runs` 做准备）

### 这一步要解决什么问题

前面你已经知道 `HealthResponse` 是 schema，但后面一进入 `POST /api/runs`，通常就不再只有一种 schema 了。

你需要先分清两件事：

1. 什么叫输入 schema
2. 什么叫输出 schema

不先分清这一点，后面很容易把“用户传进来的数据”和“接口返回出去的数据”写混。

### 代码示例

先用当前已经存在的 `HealthResponse`，再配一个“未来 `POST /api/runs` 很可能会用到”的示意例子来看：

```python
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str
    environment: str


class RunCreateRequest(BaseModel):
    job_name: str
    test_line: str
    environment: str


class RunResponse(BaseModel):
    run_id: str
    status: str
    message: str
```

### 函数调用流程图（含大概意思）

先看当前的 `GET /api/health`：

```text
请求进来（没有 body）
   |
   | 不需要接收用户提交的数据
   v
router -> service
   |
   | service 准备返回数据
   v
HealthResponse
   |
   | 只负责约束“返回给外部的数据长什么样”
   v
JSON 响应
```

再看未来的 `POST /api/runs`：

```text
请求进来（带 body）
   |
   | 先接收用户提交的数据
   v
RunCreateRequest
   |
   | 先校验输入字段是否齐全、类型是否正确
   v
router -> service
   |
   | service 真正处理创建 run 的逻辑
   v
RunResponse
   |
   | 再约束“最终返回给外部的数据长什么样”
   v
JSON 响应
```

最短记忆版：

```text
输入 schema 管“进来的数据”
输出 schema 管“出去的数据”
```

### 相关问题记录

#### 问题 1：为什么 `GET /api/health` 现在只看到了一个 schema？

因为这条接口没有请求体 body。

也就是说：

- 调用方不需要提交一坨 JSON 给你
- 所以这一步暂时不需要输入 schema
- 只需要一个输出 schema 去约束返回结果

因此 `HealthResponse` 在当前阶段，本质上是一个输出 schema。

#### 问题 2：为什么 `POST /api/runs` 往往会比 `GET /api/health` 多一个 schema？

因为 `POST` 通常会带请求体。

一旦有请求体，你就要先回答这些问题：

- 用户必须传哪些字段
- 每个字段是什么类型
- 哪些字段可以为空
- 哪些字段缺了就要报错

这时就需要一个输入 schema 来先把“进来的数据”立规矩。

然后当 service 处理完以后，你通常还要再定义一个输出 schema，去约束最终返回结果。

#### 问题 3：输入 schema 和输出 schema 能不能先写成一样？

可以，但不建议默认这么想。

因为现实里这两者经常不是一回事：

- 用户创建 run 时提交的是 `job_name / test_line / environment`
- 但接口返回时，往往还会多出 `run_id / status / created_at`

也就是说：

- 输入 schema 关心“用户应该交什么”
- 输出 schema 关心“系统最终回什么”

后面做 `POST /api/runs` 时，最好一开始就把这两个角色分开理解。

#### 问题 4：这一小步最值得记住的一句话是什么？

```text
输入 schema 先拦住和校验用户提交的数据，输出 schema 再约束和整理系统返回的数据。
```

### 涉及文件

- `platform-api/app/schemas/health.py`
- `platform-api/app/api/v1/router.py`
- `platform-api/app/services/health_service.py`

### 你自己动手时的落代码顺序

这一步还是以理解为主，不要求你新增源码。

建议你自己做下面这几个动作：

1. 回到 `health.py`，确认 `HealthResponse` 现在属于哪一种 schema
2. 自己假设一个 `POST /api/runs` 请求体，想想“用户会提交哪些字段”
3. 再想想如果 run 创建成功，接口应该返回哪些字段
4. 试着把“输入字段”和“输出字段”分成两组写在纸上或文档里

### 如何验证

这一步的验证，重点不是跑新接口，而是确认你已经能区分输入 schema 和输出 schema。

这里默认假设 Jenkins Master / 目标服务器是 Linux 环境，所以命令使用 `python3` 和 `source`。

#### 方式 A：推荐做法（Jenkins Master / 目标服务器验证）

先把现有服务跑起来，确认你还能访问已有的健康检查接口：

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

访问：

```bash
curl http://127.0.0.1:8000/api/health
```

然后对照文档，回答下面两个问题：

1. `HealthResponse` 是输入 schema 还是输出 schema
2. 如果未来要做 `POST /api/runs`，为什么大概率至少需要一个新的输入 schema

#### 方式 B：可选做法（本地验证）

如果你本机具备 Python 环境，也可以同样执行：

```powershell
cd C:\TA\jenkins_robotframework\platform-api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
curl http://127.0.0.1:8000/api/health
```

### 验收结果

- [ ] 你能区分什么是输入 schema、什么是输出 schema
- [ ] 你能判断 `HealthResponse` 现在属于输出 schema
- [ ] 你能说出为什么 `POST /api/runs` 大概率至少要新增一个输入 schema

### 我这一步学到了什么

- schema 不只是“定义一个类”，它在接口里承担的是输入约束或输出约束的角色
- 现在先把输入和输出 schema 分开理解，后面进入 `POST /api/runs` 会清楚很多

---

## Step 4：确定 `POST /api/runs` 第一版最小请求体

### 这一步要解决什么问题

现在先不急着把 `POST /api/runs` 代码写出来，而是先把一个最关键的问题定清楚：

**第一版最小请求体，到底应该只收哪几个字段？**

如果这一步不先定住，后面很容易一上来就把太多字段塞进接口里，结果既难学，也难验证。

按照你这个项目的实际业务语义：

- `testline` 本身就代表测试环境
- 所以后面不再额外单独增加 `environment` 字段

### 代码示例

第一版最小请求体，建议先只保留两个字段：

```json
{
  "testline": "5G_SA_REGRESSION",
  "robotcase_path": "cases/smoke/login.robot"
}
```

如果把它先写成输入 schema 的样子，大概会像这样：

```python
from pydantic import BaseModel


class RunCreateRequest(BaseModel):
    testline: str
    robotcase_path: str
```

### 函数调用流程图（含大概意思）

```text
automation-portal / 调用方
   |
   | 提交 testline + robotcase_path
   v
POST /api/runs
   |
   | 先由输入 schema 接住请求体
   v
RunCreateRequest
   |
   | 负责校验：字段是否齐全、类型是否正确
   v
router -> service
   |
   | 后面再由 service 决定如何映射 Jenkins job、如何触发执行
   v
run 创建结果 / 返回值
```

最短记忆版：

```text
第一版 POST /api/runs
= 告诉平台：在哪个 testline 上，执行哪个 robot case
```

### 相关问题记录

#### 问题 1：这里的 `POST /api/runs`，是不是就是“post 一个 Jenkins job 去调 Robot case”？

可以这样理解，但更准确一点：

- 前端不是直接去调 Jenkins
- 而是先调用 `platform-api` 的 `POST /api/runs`
- 再由 `platform-api` 去决定如何触发 Jenkins 上的执行逻辑

也就是说：

```text
前端 -> platform-api -> Jenkins -> Robot case
```

所以这一步的请求体，不应该一开始就暴露 Jenkins 的底层细节，而应该先保留平台自己的业务语义字段。

#### 问题 2：为什么第一版只建议放 `testline` 和 `robotcase_path`？

因为这两个字段已经回答了最核心的两个问题：

1. 这次在哪个环境上跑  
   这里用你们项目里的业务词，叫 `testline`
2. 这次跑哪个 Robot case  
   这里用 `robotcase_path`

如果第一版先把这两个字段打通，已经足够形成最小闭环。

#### 问题 3：为什么不再额外加一个 `environment` 字段？

因为你已经明确说明了：

**在这个项目里，`testline` 的实际业务含义就等同于测试环境。**

所以后续统一按下面这个语义理解：

```text
testline = environment
```

为了避免重复和混淆，后续 schema、接口、文档都优先直接使用 `testline`。

#### 问题 4：为什么第一版不直接收 `job_name`、`agent_label`、`jenkins_url` 这些字段？

因为这些更像是 Jenkins 内部实现细节，而不是前端应该直接提交的业务字段。

更推荐的分层方式是：

- 前端/调用方只提交业务语义字段
- `platform-api` 负责把业务字段映射成 Jenkins 需要的参数

也就是说，第一版更推荐让前端说：

```text
我要在这个 testline 上跑这个 robot case
```

而不是一开始就让前端自己决定：

```text
我要调哪个 Jenkins job、用哪个 agent、传哪些内部参数
```

#### 问题 5：这一小步最值得记住的一句话是什么？

```text
POST /api/runs 第一版先只收业务上最必要的两个字段：testline 和 robotcase_path。
```

### 涉及文件

- `docs/modules/platform-api/index.md`
- `platform-api/app/schemas/run.py`（下一步大概率会新增）
- `platform-api/app/api/v1/router.py`（下一步大概率会新增 `POST /api/runs`）

### 你自己动手时的落代码顺序

这一步仍然先以设计为主，不要求你立刻改源码。

建议你自己先完成这几个确认动作：

1. 确认后续统一使用 `testline`，不再单独拆 `environment`
2. 确认 `robotcase_path` 是否就是你希望前端传给平台的 case 标识方式
3. 用一句话复述：`POST /api/runs` 第一版最小请求体只收什么、为什么
4. 如果你觉得还需要第三个字段，先写下来，再判断它是不是第一版必需项

### 如何验证

这一步的验证重点不是跑新接口，而是确认请求体设计已经收敛到最小闭环。

这里默认假设 Jenkins Master / 目标服务器是 Debian 13 Linux 环境。

#### 方式 A：推荐做法（设计验证）

先不写代码，只回答下面三个问题：

1. `testline` 在你这个项目里为什么可以直接等同于环境
2. 为什么第一版不额外再收一个 `environment`
3. 为什么第一版不建议直接暴露 `job_name`

如果这三个问题都能回答清楚，说明这一步设计已经基本定住。

#### 方式 B：可选做法（为下一步做准备）

你也可以提前在 Debian 13 环境确认当前服务基础环境仍然可用：

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/api/health
```

### 验收结果

- [ ] 你能明确 `POST /api/runs` 第一版只收 `testline` 和 `robotcase_path`
- [ ] 你能明确在这个项目里 `testline = environment`
- [ ] 你能说明为什么第一版不先暴露 Jenkins 底层字段

### 我这一步学到了什么

- 设计接口时，第一版最重要的不是“字段越全越好”，而是先收敛到最小闭环
- 在这个项目里，`testline` 是核心业务词，后面应该统一沿用，而不是再并列出一个 `environment`

---

## Step 5：为 `POST /api/runs` 先设计输入 schema 和输出 schema 的第一版字段

### 这一步要解决什么问题

Step 4 已经定下来了：`POST /api/runs` 第一版最小请求体先只收：

- `testline`
- `robotcase_path`

但这还不够，因为后面真正写接口时，你还要继续回答两个问题：

1. 输入 schema 具体长什么样
2. 输出 schema 第一版具体回什么字段

这一步就是先把这两组字段分开定住。

### 代码示例

第一版输入 schema，建议先这样：

```python
from pydantic import BaseModel


class RunCreateRequest(BaseModel):
    testline: str
    robotcase_path: str
```

第一版输出 schema，建议先这样：

```python
from pydantic import BaseModel


class RunCreateResponse(BaseModel):
    run_id: str
    status: str
    message: str
```

如果把它们放在一起看，就是：

```python
from pydantic import BaseModel


class RunCreateRequest(BaseModel):
    testline: str
    robotcase_path: str


class RunCreateResponse(BaseModel):
    run_id: str
    status: str
    message: str
```

### 函数调用流程图（含大概意思）

```text
调用方 / automation-portal
   |
   | 提交 testline + robotcase_path
   v
RunCreateRequest
   |
   | 负责拦住输入，校验字段是否齐全、类型是否正确
   v
POST /api/runs -> router -> service
   |
   | service 负责创建 run，并准备结果
   v
RunCreateResponse
   |
   | 负责约束最终返回字段
   v
JSON 响应
```

最短记忆版：

```text
输入 schema 决定“前端必须交什么”
输出 schema 决定“平台最终回什么”
```

### 相关问题记录

#### 问题 1：为什么输入 schema 第一版还是只保留两个字段？

因为 Step 4 已经确认了第一版最小闭环的目标：

```text
在哪个 testline 上，执行哪个 robot case
```

这对应到输入字段，就是：

- `testline`
- `robotcase_path`

如果这一步再额外加版本号、标签、参数、触发人，就会让第一版接口过早变复杂。

#### 问题 2：为什么输出 schema 第一版建议先回 `run_id`、`status`、`message`？

因为这三个字段已经足够表达“平台有没有接住这次请求，以及后续该怎么追踪它”。

它们分别回答：

1. `run_id`  
   这次请求在平台里的唯一标识是什么
2. `status`  
   当前这次 run 处于什么状态，例如 `queued`、`created`、`triggered`
3. `message`  
   给调用方一个最简单的人类可读说明

这三个字段已经足够支撑第一版最小响应。

#### 问题 3：为什么第一版输出 schema 不先加 `jenkins_build_number`？

因为第一版的重点是先把 `platform-api` 自己的 run 创建语义站稳。

在更合理的分层里：

- `run_id` 是平台自己的 ID
- `jenkins_build_number` 是后面真的触发 Jenkins 后，才可能追加的外部执行信息

也就是说，前期最好先把“平台内部主键”和“Jenkins 外部构建号”分开，不要一开始就绑死。

#### 问题 4：`status` 第一版最推荐用什么值？

第一版只要先保持简单和稳定就可以。

如果只是“平台已经接住创建请求，但还没深入做更多逻辑”，比较容易理解的值可以是：

- `created`

如果你想强调“后面还要排队或触发 Jenkins”，也可以是：

- `queued`

当前阶段先不用过度设计状态机，只要先统一一个最小状态词即可。

#### 问题 5：这一小步最值得记住的一句话是什么？

```text
RunCreateRequest 先定义“用户要交什么”，RunCreateResponse 再定义“平台回什么”。
```

### 涉及文件

- `docs/modules/platform-api/index.md`
- `platform-api/app/schemas/run.py`（下一步很可能会新增）
- `platform-api/app/api/v1/router.py`（下一步会开始用到）

### 你自己动手时的落代码顺序

这一步仍然先以设计为主，不要求你马上把源码写出来。

建议你自己先完成这几个动作：

1. 先把 `RunCreateRequest` 的两个字段抄出来，看是否都属于“前端必须提交的信息”
2. 再把 `RunCreateResponse` 的三个字段抄出来，看是否都属于“平台应该返回的信息”
3. 自己判断：`run_id` 为什么属于输出，而不属于输入
4. 如果你想加第 4 个输出字段，先写下来，再判断它是不是第一版必需项

### 如何验证

这一步的验证重点不是跑新接口，而是确认输入字段和输出字段已经分组清楚。

这里默认假设 Jenkins Master / 目标服务器是 Debian 13 Linux 环境。

#### 方式 A：推荐做法（设计验证）

先不写代码，只回答下面四个问题：

1. 为什么 `testline` 和 `robotcase_path` 属于输入 schema
2. 为什么 `run_id` 属于输出 schema
3. 为什么第一版输出 schema 先不急着加 Jenkins 构建号
4. `status` 第一版为什么只需要一个最小状态词

如果这四个问题都能回答清楚，说明这一步的字段设计已经比较稳定。

#### 方式 B：可选做法（为下一步做准备）

你也可以继续在 Debian 13 环境确认当前基础服务仍然可用：

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/api/health
```

### 验收结果

- [ ] 你能明确 `RunCreateRequest` 第一版只收 `testline` 和 `robotcase_path`
- [ ] 你能明确 `RunCreateResponse` 第一版先回 `run_id`、`status`、`message`
- [ ] 你能说明为什么输入 schema 和输出 schema 不能混写

### 我这一步学到了什么

- 设计 POST 接口时，输入 schema 和输出 schema 最好一开始就分开，不然后面很容易混乱
- 第一版输出 schema 先表达“平台是否成功接住请求”即可，不必过早塞进 Jenkins 细节

---

## Step 6：先确定 `POST /api/runs` 第一版最小返回语义

### 这一步要解决什么问题

Step 5 已经把输入 schema 和输出 schema 的字段先定下来了：

- 输入：`testline`、`robotcase_path`
- 输出：`run_id`、`status`、`message`

但还差最后一个很关键的问题：

**`status` 第一版到底应该返回什么值，`message` 又应该怎么表达到最合适？**

如果这一步不先统一，后面即使代码写出来了，也容易出现：

- 有人写 `created`
- 有人写 `queued`
- 有人写 `success`
- 有人写一大段不统一的 message

所以这里先把第一版最小返回语义定下来。

### 代码示例

第一版推荐先把返回值设计成这样：

```json
{
  "run_id": "run-20260421-0001",
  "status": "created",
  "message": "Run request accepted."
}
```

如果写成 schema 使用时的样子，大概会像这样：

```python
from pydantic import BaseModel


class RunCreateResponse(BaseModel):
    run_id: str
    status: str
    message: str
```

### 函数调用流程图（含大概意思）

```text
调用方发起 POST /api/runs
   |
   | platform-api 接住请求
   v
router -> service
   |
   | service 先生成平台自己的 run_id
   | 并确认“这次创建请求已被平台接住”
   v
RunCreateResponse
   |
   | 返回最小语义：
   | run_id = 这次 run 的平台标识
   | status = 当前最小状态
   | message = 给调用方的简短说明
   v
JSON 响应
```

最短记忆版：

```text
第一版先表达“平台已经成功接住这次 run 创建请求”。
```

### 相关问题记录

#### 问题 1：为什么第一版推荐 `status = created`？

因为当前阶段最重要的是表达：

```text
这次 run 创建请求，平台已经接住了。
```

`created` 的好处是语义稳定、容易理解，而且不会过早假设后面一定已经完成了 Jenkins 触发。

你可以把它理解成：

- 不是“执行成功”
- 不是“Jenkins 已完成”
- 而是“平台里的 run 记录已经创建出来了”

#### 问题 2：那为什么不是 `success`？

因为 `success` 很容易让人误解成：

- Robot case 已经执行成功
- 或者 Jenkins job 已经跑完成功

但在 `POST /api/runs` 刚返回的那一刻，通常这些事情都还没有发生。

所以第一版更推荐：

- `created`

而不是：

- `success`

#### 问题 3：那为什么不是 `queued`？

`queued` 也不是不行，但它更适合你已经明确做了“排队 / 异步调度”这层语义的时候。

如果你当前这一步只是先把：

- 平台接请求
- 生成 `run_id`
- 返回最小结果

这三件事打通，那么 `created` 会更稳、更中性。

后面如果你把“创建 run 后立刻进入调度队列”这个动作真正做实了，再把状态从 `created` 扩展到 `queued` 会更自然。

#### 问题 4：第一版 `message` 最推荐写成什么风格？

建议保持：

- 简短
- 稳定
- 不夹带太多实现细节

例如：

```text
Run request accepted.
```

不建议第一版就写成很长、很细的句子，比如：

```text
Run was successfully created and will be sent to Jenkins for execution on selected testline...
```

因为后面流程变化时，这种 message 很容易失真。

#### 问题 5：这一小步最值得记住的一句话是什么？

```text
POST /api/runs 第一版先返回“平台已接住请求”，不要误写成“执行已经成功”。
```

### 涉及文件

- `docs/modules/platform-api/index.md`
- `platform-api/app/schemas/run.py`
- `platform-api/app/services/`（下一步真正实现时会开始用到）

### 你自己动手时的落代码顺序

这一步还是先以语义设计为主，不要求你立刻改源码。

建议你自己先完成这几个动作：

1. 想一想 `created` 和 `success` 在语义上最大的差别是什么
2. 再想一想为什么当前阶段先不用 `queued`
3. 自己写一版最短 `message`
4. 用一句话复述：`POST /api/runs` 第一版返回语义到底想表达什么

### 如何验证

这一步的验证重点不是跑新接口，而是确认你已经把返回语义定清楚。

这里默认假设 Jenkins Master / 目标服务器是 Debian 13 Linux 环境。

#### 方式 A：推荐做法（设计验证）

先不写代码，只回答下面三个问题：

1. 为什么第一版 `status` 不推荐写成 `success`
2. 为什么当前阶段 `created` 比 `queued` 更稳妥
3. 为什么 `message` 应该保持简短和中性

如果这三个问题都能回答清楚，说明这一步语义已经比较稳定。

#### 方式 B：可选做法（为下一步做准备）

继续保持现有基础服务可访问即可：

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/api/health
```

### 验收结果

- [ ] 你能明确第一版 `status` 推荐先用 `created`
- [ ] 你能说明为什么 `success` 不适合出现在 `POST /api/runs` 刚返回时
- [ ] 你能写出一条简短、稳定的 `message`

### 我这一步学到了什么

- 设计返回值时，最重要的是语义准确，不要让调用方误以为执行已经完成
- 第一版接口先稳定表达“请求已接住”，后面再逐步扩展到排队、触发、执行、完成等状态

---

## Step 7：接入 SQLite，让 `POST /api/runs` 真正创建 run 记录

### 这一步要解决什么问题

前面的 `POST /api/runs` 虽然已经有了输入 schema 和返回语义，但代码还是静态 stub。

这会带来两个问题：

1. 每次返回的 `run_id` 都没有真实创建动作支撑
2. 后面的 `GET /api/runs` 和 `GET /api/runs/{run_id}` 没有数据来源

所以这一步要把链路推进成真正的最小闭环：

- 接口收到请求
- service 生成平台自己的 `run_id`
- repository 把最小 run 元数据写进 `SQLite`
- 接口返回统一的创建结果

### 代码示例

```python
# app/main.py
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import router as api_router
from app.core.config import settings
from app.repositories.run_repository import initialize_run_repository


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_run_repository()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api")
```

```python
# app/services/run_service.py
import sqlite3
from datetime import datetime
from zoneinfo import ZoneInfo

from app.repositories.run_repository import insert_run_record
from app.schemas.run import RunCreateRequest, RunCreateResponse


def _build_run_id(timestamp: str, sequence: int) -> str:
    return f"run-{timestamp}-{sequence:02d}"


def run_create(request: RunCreateRequest) -> RunCreateResponse:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    timestamp = now.strftime('%Y%m%d%H%M%S%f')[:-3]

    record = {
        "testline": request.testline,
        "robotcase_path": request.robotcase_path,
        "status": "created",
        "message": "Run request accepted.",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    for sequence in range(1, 1000):
        record["run_id"] = _build_run_id(timestamp, sequence)
        try:
            insert_run_record(record)
            break
        except sqlite3.IntegrityError:
            continue

    return RunCreateResponse(
        run_id=record["run_id"],
        status=record["status"],
        message=record["message"],
    )
```

```python
# app/repositories/run_repository.py
import sqlite3
from pathlib import Path

from app.core.config import settings


def initialize_run_repository() -> None:
    db_path = Path(settings.runs_db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                testline TEXT NOT NULL,
                robotcase_path TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            '''
        )
        connection.commit()
```

### 函数调用流程图（含大概意思）

```text
调用方发起 POST /api/runs
   |
   | 请求体先进入 router
   v
create_run(request)
   |
   | router 把校验后的 schema 交给 service
   v
run_create(request)
   |
   | service 生成 run_id、补 created/status/message/时间戳
   | 并把最小记录组装成 record
   v
insert_run_record(record)
   |
   | repository 负责建表（如未建）并写入 SQLite
   v
runs 表
   |
   | service 返回最小响应模型
   v
RunCreateResponse -> JSON
```

### 相关问题记录

#### 问题 1：为什么这一步先接 `SQLite`，而不是直接接 Jenkins？

因为当前更需要先把平台自己的 run 元数据落稳。

先有稳定的 run 记录，后面再接：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- Jenkins 回写状态

才不会没有数据基线。

#### 问题 2：为什么要单独加 repository 层？

因为这一步开始已经出现“数据落库”职责了。

如果继续把 `sqlite3` 细节写在 router 或 service 里，后面扩展列表查询、详情查询、状态更新时会越来越乱。

当前先拆成：

- router：接 HTTP 请求
- service：组装业务语义
- repository：负责和 SQLite 交互

后面接 Jenkins 或换数据库时，这个分层会更稳。

#### 问题 3：为什么返回给调用方的字段还是只保留 `run_id / status / message`？

因为当前这一步的目标是先把“创建成功并已入库”打通，不是把详情接口一次性做完。

像 `created_at`、`robotcase_path` 这些信息已经存进库里了，更适合放到后续的列表和详情接口里返回。

#### 问题 4：`core/` 目录是干什么用的？

可以把 `core/` 理解成“全局底座层”。

它不负责某一个具体业务，而是放整个应用都会用到的基础能力。

当前这个项目里，最典型的例子就是：

- `app/core/config.py`

它负责统一读取和保存全局配置，例如：

- `app_name`
- `app_env`
- `app_host`
- `app_port`
- `runs_db_path`

最短记忆版：

```text
core = 全局公共基础层，不是某个具体业务层
```

#### 问题 5：以后和 `SQLite` 相关的代码，是不是都统一写到 `repository/` 下面？

可以先记一个最稳的划分：

- `core/`：放数据库路径这类全局配置
- `repository/`：放 SQL、建表、查询、插入、更新
- `service/`：决定什么时候查库、什么时候写库、写什么业务语义

所以不是“只要和 SQLite 沾边就全塞到 repository”，而是：

- 数据访问动作放 `repository`
- 业务决策放 `service`
- 全局配置放 `core`

后面 `repository/` 里还可以继续放：

- `run_repository.py`
- `artifact_repository.py`
- `kpi_repository.py`

也就是说，`repository` 后续不只是放当前这一份 run 落库代码，而是专门负责整个平台的持久化访问层。

#### 问题 6：通俗地说，当前这条 `SQLite` 流程到底是怎么走的？

可以直接把它想成一句话：

```text
接口收到请求后，service 先整理好一条 run 记录，再交给 repository 写进本地 .db 文件。
```

按最口语的顺序走一遍就是：

1. 调用方发 `POST /api/runs`
2. `router` 接住请求
3. `schema` 先校验请求体长得对不对
4. `service` 生成这次自己的 `run_id`
5. `service` 把要保存的数据整理成一条 record
6. `repository` 打开 `SQLite` 的 `.db` 文件
7. 如果 `runs` 表还没有，就先建表
8. 然后把这条 record 插进去
9. 最后接口把 `run_id / status / message` 返回给调用方

如果你想用更生活化的方式记：

- `router` 像前台接待
- `schema` 像表单检查员
- `service` 像业务同事，决定这次要记什么
- `repository` 像录入员，真的去写账本
- `SQLite` 就是那个本地账本文件

#### 问题 7：为什么现在不用 `UTC`，也不再在 `run_id` 后面拼随机短串？

这次调整主要是为了让当前阶段的 `run_id` 更符合你的使用习惯，也更容易人工排查。

现在改成了：

- 时间使用 `CST`（`Asia/Shanghai`）
- `run_id` 默认先用 `run-时间戳`
- 时间戳精度提升到毫秒
- 如果插入冲突，再补 `-01 / -02` 这类短序号

也就是像这样：

```text
run-20260422104958123
```

这样改的好处是：

```text
既保留时间戳的可读性，也给后续冲突重试留出了空间
```

如果同一时间戳下第一次插入冲突，就继续尝试：

```text
run-20260422104958123
   -> run-20260422104958123-01
   -> run-20260422104958123-02
```

这样比拼一段随机串更直观，也更方便人工排查。

### 涉及文件

- `platform-api/app/main.py`
- `platform-api/app/core/config.py`
- `platform-api/app/api/v1/router.py`
- `platform-api/app/schemas/run.py`
- `platform-api/app/services/run_service.py`
- `platform-api/app/repositories/run_repository.py`
- `platform-api/tests/test_runs.py`
- `platform-api/.env.example`

### 你自己动手时的落代码顺序

1. 在配置层补 `RUNS_DB_PATH`
2. 新增 `run_repository`，先把建表和插入能力写好
3. 改 `run_service`，让它生成真实 `run_id` 并调用 repository
4. 改 `router`，让它直接返回 service 产出的响应模型
5. 在 `main.py` 的启动阶段初始化 run 表
6. 增加 `POST /api/runs` 的 API 测试，确认响应和落库都成立

### 如何验证

先在 Jenkins Master / 目标服务器执行：

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests/test_health.py tests/test_runs.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端验证：

```bash
curl -X POST http://127.0.0.1:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"testline":"smoke","robotcase_path":"cases/login.robot"}'
```

默认数据库文件会落在：

```text
platform-api/data/results/automation_platform.db
```

如果在 Windows 本地验证，可用：

```powershell
cd C:\TA\jenkins_robotframework\platform-api
python -m pytest tests/test_health.py tests/test_runs.py
```

### 验收结果

- [x] `POST /api/runs` 不再返回固定写死的 `run_id`
- [x] `POST /api/runs` 会把最小 run 元数据写入 `SQLite`
- [x] 启动 FastAPI 时会自动初始化 `runs` 表
- [x] 已有 API 级测试覆盖“创建并落库”这条最小链路

### 我这一步学到了什么

- `POST /api/runs` 的“最小可用”不只是返回 JSON，而是要真的生成 run 记录
- 一旦开始有持久化需求，就应该把 HTTP、业务语义、数据访问三层职责分开
- 现在 `platform-api` 已经具备了后续继续实现列表、详情、Jenkins 回写的基础数据面

### 复盘问题（你来回答）

#### 题目 1：复述调用链

请你用自己的话复述一下这条链路：

```text
POST /api/runs 从收到请求开始，到最后把数据写进 SQLite 并返回响应，中间依次经过了哪几层？每一层大概负责什么？
```
Stella: 
runs请求先到API,到对应的Router接住这个请求，Schemas校验输入，然后到Services创建Run id等信息给Schemas校验输出，同时Services将Run id等信息整理成一条record，repository负责把这条record记录到sqlite db.

#### 题目 2：字段职责题

请说明下面这些字段分别是谁负责、主要用途是什么：

- `testline`
- `robotcase_path`
- `run_id`
- `status`
- `message`
- `created_at`
- `updated_at`

重点说清：

- 哪些是请求传进来的
- 哪些是服务端生成的
- 哪些是先入库但暂时不对外返回的

Stella: testline和robotcase_path是请求传进来的，后面几个都是服务端生成，目前只返回run_id，status， message


#### 题目 3：判断题

判断下面说法对不对，并简单说明原因：

1. `router` 这一层适合直接写 `sqlite3.connect(...)`，因为这样少绕一层。
  no 
2. `service` 这一层主要负责组装业务语义，比如生成 `run_id`、补状态字段。
yes
3. `repository` 这一层主要负责和数据库打交道。
yes
4. `core/config.py` 主要是 run 业务逻辑层的一部分。
no

#### 题目 4：改错题

假设有人把代码改成下面这种思路：

- `router` 里直接生成 `run_id`
- `router` 里直接写 SQL
- `service` 只剩下一层空转调用
- `repository` 删掉

请说说这套改法最主要有哪两个问题。
分工不明确 后续代码逻辑容易混乱

#### 题目 5：场景题

如果后面要继续做 `GET /api/runs`，你觉得最应该优先新增到哪一层的方法？

可以按这个格式回答：

- `repository` 里加什么
get好像用不到db?
- `service` 里加什么
  如何get run result的实现 
- `router` 里加什么
  get run result

不用写代码，只说职责。

#### 题目 6：通俗解释题

请你用这套比喻，再讲一遍当前的 `SQLite` 流程：

- 前台接待
route
- 表单检查
schemas
- 业务同事
services
- 录入员
repositories
- 账本
sqlite db存储

#### 题目 7：小判断题

为什么这一步返回给前端的还是只有：

- `run_id`
- `status`
- `message`

而不是把 `created_at`、`robotcase_path` 也一起直接返回？

请说出你理解的设计考虑。
还没有真实接jenkins跑case

#### 题目 8：轻微变形题

现在 `run_id` 改成了 `CST + 毫秒时间戳`。

如果以后真的出现“同一毫秒内连续创建两条 run”这种极端情况，你觉得可以往哪个方向改，既尽量保留可读性，又降低重复风险？
Stella: 我认为同一毫秒内连续创建两条 run也并没有什么影响啊 会创建不起来还是？

不用写标准答案，说你的思路就行。

### 你的答案

#### 题目 1

<你填写>

#### 题目 2

<你填写>

#### 题目 3

<你填写>

#### 题目 4

<你填写>

#### 题目 5

<你填写>

#### 题目 6

<你填写>

#### 题目 7

<你填写>

#### 题目 8

<你填写>

### 我的 Review 结论

#### 这轮答得比较稳的点

- 你已经能复述出主链路：`router -> schema -> service -> repository -> SQLite`
- 你已经知道 `testline`、`robotcase_path` 是请求传入，`run_id / status / message` 是服务端生成
- 你已经知道 `router` 不应该直接写 `sqlite3.connect(...)`
- 你已经知道 `service` 负责业务语义，`repository` 负责数据库访问，`core` 不是 run 业务层

#### 这轮最需要补强的点

1. `GET /api/runs` 当然还是要用数据库

你在题目 5 里写了“get 好像用不到 db?”，这里要尽快纠正。

因为当前 run 数据就是存在 `SQLite` 里的，所以后面无论是：

- `GET /api/runs`
- `GET /api/runs/{run_id}`

本质上都要去数据库里把数据查出来。

2. 题目 7 的理解还不够完整

你写“还没有真实接 Jenkins 跑 case”，这个方向不算错，但还不够到位。

当前只返回 `run_id / status / message`，更核心的原因是：

- 这一步的目标是先打通“最小创建语义”
- 不是一步把详情接口也做完
- 像 `created_at`、`robotcase_path` 这种信息虽然已经入库，但更适合留给后续列表 / 详情接口去返回

也就是说，这里重点是“接口职责收敛”，不只是“Jenkins 还没接”。

3. 题目 8 还没真正回答到点上

你问“会创建不起来还是？”，这说明你已经意识到可能有冲突风险，但还没把后果说清。

如果同一毫秒内生成了完全相同的 `run_id`，最直接的问题就是：

- 主键冲突
- 插入失败

因为当前 `runs` 表里：

- `run_id` 是主键

所以后面要继续考虑“如何在保留可读性的同时避免重复”。

#### 表达上的小建议

后面答题时，尽量不要只写：

- `yes`
- `no`
- “分工不明确”

因为这样虽然方向可能是对的，但不方便你自己回看，也不方便我判断你到底是“真的理解”还是“刚好猜对”。

更好的写法是每题至少补一句“为什么”。

### 最优答案（Review 后沉淀）

#### 题目 1：复述调用链

`POST /api/runs` 进来后，先由 `router` 接住 HTTP 请求；请求体先按 `RunCreateRequest` 做输入校验；然后 `service` 负责生成 `run_id`、补 `status / message / created_at / updated_at`，并组装成一条 record；再交给 `repository` 去操作 `SQLite`，如果表不存在就先建表，再把 record 插入 `runs` 表；最后 `service` 返回 `RunCreateResponse`，由接口返回给调用方。

最短记忆版：

```text
router 接请求，schema 做校验，service 组装业务数据，repository 写入 SQLite，最后返回最小响应。
```

#### 题目 2：字段职责题

- `testline`：请求传入，表示这次 run 选中的测试线
- `robotcase_path`：请求传入，表示这次要跑的 Robot case 路径
- `run_id`：服务端生成，作为这次 run 的平台唯一标识
- `status`：服务端生成，当前第一版固定表达为 `created`
- `message`：服务端生成，给调用方一个简短稳定的说明
- `created_at`：服务端生成，记录创建时间
- `updated_at`：服务端生成，记录更新时间

当前对外返回：

- `run_id`
- `status`
- `message`

当前先入库但暂时不对外返回：

- `created_at`
- `updated_at`
- `testline`
- `robotcase_path`

#### 题目 3：判断题

1. `router` 这一层适合直接写 `sqlite3.connect(...)`，因为这样少绕一层。

错误。`router` 主要负责 HTTP 接入，如果把数据库细节写进来，会让接口层和持久化层耦合，后面会越来越乱。

2. `service` 这一层主要负责组装业务语义，比如生成 `run_id`、补状态字段。

正确。`service` 的职责就是把输入变成业务上真正需要落地的数据。

3. `repository` 这一层主要负责和数据库打交道。

正确。它负责建表、插入、查询、更新等持久化动作。

4. `core/config.py` 主要是 run 业务逻辑层的一部分。

错误。`core/config.py` 属于全局基础配置层，不是 run 的业务逻辑层。

#### 题目 4：改错题

如果把 `run_id` 生成和 SQL 都塞进 `router`，再删掉 `repository`，最主要会有两个问题：

1. 分层职责被打乱

`router` 本来只该处理 HTTP，现在却同时承担业务逻辑和数据库访问，代码会越来越难维护。

2. 后续扩展会很痛苦

以后只要加：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- 更新状态
- 换数据库

都会被迫继续在 `router` 里堆逻辑，代码很快会失控。

#### 题目 5：场景题

如果后面做 `GET /api/runs`，建议优先这样拆：

- `repository`：增加查询 runs 列表的方法，例如 `list_runs()`
- `service`：增加组装列表返回结果的方法，例如 `get_runs()`
- `router`：增加 `GET /api/runs` 路由，把请求交给 service，再把结果返回给调用方

最关键的一点是：

```text
GET /api/runs` 当然也要查数据库，因为当前 run 数据就是存放在 SQLite 里的。
```

#### 题目 6：通俗解释题

可以这样记：

- `router` 是前台接待，先把请求接住
- `schema` 是表单检查员，确认请求格式对不对
- `service` 是业务同事，决定这次 run 要记哪些信息
- `repository` 是录入员，真的去把这条记录写进账本
- `SQLite` 就是那个本地账本文件

整条链路就是：

```text
前台接到申请 -> 检查表单 -> 业务同事整理内容 -> 录入员写到账本 -> 返回受理结果
```

#### 题目 7：为什么当前只返回 `run_id / status / message`

因为这一步的目标是先把“最小创建闭环”打通，而不是一步做完整详情接口。

所以当前接口只需要稳定表达：

```text
这次 run 请求平台已经接住，并且 run 记录已经创建成功。
```

像下面这些信息虽然已经入库：

- `created_at`
- `updated_at`
- `testline`
- `robotcase_path`

但更适合放到后续的列表接口和详情接口里返回，而不是在创建接口里一次性全塞出来。

#### 题目 8：如果同一毫秒内重复，怎么办？

如果同一毫秒内真的生成了两条完全相同的 `run_id`，就可能导致：

- `run_id` 主键冲突
- 插入失败

后续可以考虑几种改法，同时尽量保留可读性：

1. 先直接使用可读时间戳，如果冲突，再在后面加一个很短的递增序号

例如：

```text
run-20260422104958123
run-20260422104958123-01
```

2. 在时间戳后面加一个更短、更可读的补充片段

例如只保留 2 到 3 位短后缀，而不是很长的随机串。

3. 把“可读 `run_id`”和“数据库内部主键”分开

例如数据库内部用自增整数或 UUID，外部展示仍然保留可读时间戳。

当前阶段最实用的思路通常是第 1 种：

```text
先用时间戳，冲突时再补短序号
```

这样既保留可读性，也能降低重复风险。

---

## Step 8：实现 `GET /api/runs`，把已创建的 run 列表查出来

### 这一步要解决什么问题

前一步已经把 `POST /api/runs` 打通了，平台现在能把 run 记录写进 `SQLite`。

但如果只有“能写入”，还不够形成真正可观察的最小闭环，因为：

1. 调用方还看不到当前已经创建过哪些 run
2. 后续前端列表页没有数据来源
3. 也没法确认数据库里写进去的数据到底能不能再被读出来

所以这一步要补的不是新业务语义，而是最小查询能力：

- 从 `SQLite` 把 run 列表读出来
- 通过 `GET /api/runs` 返回给调用方
- 先按最新创建时间倒序返回

### 代码示例

```python
# app/repositories/run_repository.py
def list_run_records() -> list[dict[str, str]]:
    initialize_run_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                run_id,
                testline,
                robotcase_path,
                status,
                message,
                created_at,
                updated_at
            FROM runs
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [dict(row) for row in rows]
```

```python
# app/services/run_service.py
def get_run_list() -> RunListResponse:
    records = list_run_records()
    return RunListResponse(items=[RunListItem(**record) for record in records])
```

```python
# app/api/v1/router.py
@router.get("/runs", response_model=RunListResponse, tags=["run"])
def list_runs() -> RunListResponse:
    return get_run_list()
```

### 函数调用流程图（含大概意思）

```text
调用方发起 GET /api/runs
   |
   | 请求先进入 router
   v
list_runs()
   |
   | router 把查询动作交给 service
   v
get_run_list()
   |
   | service 调 repository 查数据库
   | 再把结果组装成响应 schema
   v
list_run_records()
   |
   | repository 从 SQLite 查询 runs 表
   | 并按 created_at 倒序返回
   v
RunListResponse -> JSON
```

### 相关问题记录

#### 问题 1：为什么 `GET /api/runs` 一定要查数据库？

因为当前 run 数据就是存放在 `SQLite` 里的。

也就是说，列表接口的数据来源不是：

- 内存里的临时变量
- router 里手写的假数据

而是：

- `runs` 表里已经真实保存的记录

所以 `GET /api/runs` 的关键就是：

```text
把之前写进 SQLite 的 run 记录，再查出来返回。
```

#### 问题 2：为什么这一版先返回 `items`，而不是直接返回一个裸数组？

因为用 `items` 包一层，会更方便后面逐步扩展。

例如后续如果你想加：

- `total`
- 分页信息
- 筛选条件回显

就不需要把接口结构整体推倒重来。

当前先保持：

```json
{
  "items": [
    {
      "run_id": "run-20260422104958123",
      "testline": "smoke",
      "robotcase_path": "cases/login.robot",
      "status": "created",
      "message": "Run request accepted.",
      "created_at": "2026-04-22T10:49:58.123+08:00",
      "updated_at": "2026-04-22T10:49:58.123+08:00"
    }
  ]
}
```

#### 问题 3：为什么列表接口现在就把 `created_at`、`updated_at` 返回出来？

因为到了列表视角，这些字段已经有直接展示价值了。

创建接口里不急着返回这些字段，是因为它的重点是“创建成功”。

但到了列表接口：

- `created_at` 可以帮助判断最近创建顺序
- `updated_at` 可以为后续状态变化展示做准备
- `testline / robotcase_path / status` 这些字段本来就是列表页最基础的信息

所以这一步把这些字段放进列表项里是合理的。

#### 问题 4：为什么 `GET /api/health` 的 router 写法和 `POST /api/runs`、`GET /api/runs` 不一样？

因为现在这两类 service 的返回值类型不一样：

- `health_service` 返回的是普通 `dict`
- `run_service` 已经直接返回 `RunCreateResponse` / `RunListResponse` 这类 schema 实例

所以 router 才会出现两种写法：

```python
# health
return HealthResponse(**get_health_payload())

# runs
return run_create(request)
return get_run_list()
```

这里并不是说 `runs` 没有经过 schema 校验，而是它的 schema 组装动作已经提前放到了 service 里。

可以这样理解：

- 第一种写法：service 返回 `dict`，router 再包成 schema
- 第二种写法：service 直接返回 schema，router 直接 `return`

当前我们决定后续统一采用第二种写法，也就是：

```text
service 负责把结果组装成 schema，router 只负责直接返回。
```

这样更符合现在 `run` 相关接口的分层思路。

`GET /api/health` 这条链路当前保持原样，不专门为了统一风格去改它。

如果你还是会混“schema 到底在哪一步参与”，可以把这条链路想成：

```text
进门检查一次，service 里整理一次，出门前再核对一次
```

最容易混的点是：

```text
schema 不是只在最后某一个点突然出现一次，而是可能在请求进来和响应出去这两头都参与。
```

以 `POST /api/runs` 为例，可以结合代码这样理解：

1. 请求进门

调用方先发一个 JSON 请求体过来。

2. FastAPI 先按输入 schema 检查

因为 router 里写的是：

```python
@router.post("/runs", response_model=RunCreateResponse, tags=["run"])
def create_run(request: RunCreateRequest) -> RunCreateResponse:
    return run_create(request)
```

这里的：

- `request: RunCreateRequest`

就表示：

```text
在真正进入 create_run() 之前，FastAPI 会先把请求体按 RunCreateRequest 解析和校验。
```

所以这是第一层 schema：

- `RunCreateRequest`
- 作用：校验输入

3. service 做业务处理

进入 `run_create()` 后，service 负责：

- 生成 `run_id`
- 补 `status / message / created_at / updated_at`
- 组装 record
- 写入数据库

4. service 主动组装输出 schema

在 `run_service.py` 里，现在不是返回普通 `dict`，而是直接返回：

```python
return RunCreateResponse(
    run_id=record["run_id"],
    status=record["status"],
    message=record["message"],
)
```

这里就是第二层 schema：

- `RunCreateResponse`
- 作用：service 自己把业务结果整理成标准响应对象

5. router 直接 return

因为 service 已经把结果组装成 schema 了，所以 router 不需要再写：

```python
RunCreateResponse(**run_create(request))
```

直接：

```python
return run_create(request)
```

就够了。

6. FastAPI 出门前再按 `response_model` 处理

router 上还写了：

- `response_model=RunCreateResponse`

这表示响应发出去前，FastAPI 还会按这个模型做最终的序列化和约束。

所以对 `POST /api/runs` 来说，更准确的顺序其实是：

```text
请求进来
-> RunCreateRequest 先校验输入
-> service 做业务处理
-> service 组装 RunCreateResponse
-> FastAPI 按 response_model 再输出
```

这也是为什么“service 再返回由 schemas 校验”这句话只说对了一半。

更准确的说法应该是：

```text
输入 schema 在请求进入 router 之前就已经参与了；
输出 schema 在 service 返回时就已经被主动组装了；
FastAPI 在响应发出去前还会再按 response_model 做最终处理。
```

你也可以把它再记成一个更形象的快递站比喻：

1. 寄件人来寄东西
2. 前台先检查寄件单格式对不对
3. 后台工作人员处理业务
4. 工作人员把回执单按固定模板填好
5. 出门前窗口再按标准格式打印给寄件人

对应关系就是：

- 输入 schema = 进门表单检查
- service 里的输出 schema = 后台把结果整理成标准回执
- `response_model` = 出门前再按标准格式发出去

最短记忆版：

```text
输入 schema：请求进来时检查
输出 schema：service 返回时组装
response_model：响应出去前再约束一次
```

### 涉及文件

- `platform-api/app/api/v1/router.py`
- `platform-api/app/schemas/run.py`
- `platform-api/app/services/run_service.py`
- `platform-api/app/repositories/run_repository.py`
- `platform-api/tests/conftest.py`
- `platform-api/tests/test_runs.py`
- `platform-api/pytest.ini`
- `platform-api/requirements.txt`
- `platform-api/README.md`

### 你自己动手时的落代码顺序

1. 在 `schemas/run.py` 里补列表接口需要的响应模型
2. 在 `run_repository.py` 里补 `list_run_records()`
3. 在 `run_service.py` 里补 `get_run_list()`
4. 在 `router.py` 里补 `GET /api/runs`
5. 增加 API 测试，确认列表真的从数据库返回，并按最新创建时间倒序

### 如何验证

先在 Jenkins Master / 目标服务器执行：

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests/test_health.py tests/test_runs.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端验证：

```bash
curl -X POST http://127.0.0.1:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"testline":"smoke","robotcase_path":"cases/login.robot"}'

curl -X POST http://127.0.0.1:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"testline":"regression","robotcase_path":"cases/payment.robot"}'

curl http://127.0.0.1:8000/api/runs
```

如果在 Windows 本地验证，可用：

```powershell
cd C:\TA\jenkins_robotframework\platform-api
python -m pytest tests/test_health.py tests/test_runs.py
```

### 验收结果

- [x] `GET /api/runs` 已经落地
- [x] 列表接口会真正从 `SQLite` 查询 `runs` 表
- [x] 列表接口会按 `created_at` 倒序返回
- [x] 已有测试覆盖“创建两条 run 后再查列表”这条链路

### 我这一步学到了什么

- “能写入数据库”和“能从数据库读出来”是两个不同的闭环，列表接口补上后，run 的最小数据面才更完整
- 列表接口不是再做一遍创建接口，而是把已有持久化数据转换成适合展示的响应结构
- 用 `items` 包一层响应对象，会让后续分页、筛选、扩展字段更自然

### 复盘问题（你来回答）

#### 题目 1

请你用自己的话复述一下 `GET /api/runs` 这条链路：请求从哪里进来，经过哪几层，最后为什么一定会落到 `SQLite` 查询？

##### 你的答案

<你填写>请求到API到router到services,再由repositories从sqlite中查询出run信息，services再返回由schemas校验 --返回调用方JSON

##### 我的 Review

主方向是对的，你已经抓住了：

- 请求先到 `router`
- 再到 `service`
- 再到 `repository`
- 最后一定要查 `SQLite`

这题还差一点点更完整：

1. 你没有明确说出为什么一定会落到 `SQLite`

核心原因是：

```text
当前 run 列表的真实数据来源，就是前面 POST /api/runs 已经写进 runs 表的记录。
```

2. 你写“services 再返回由 schemas 校验”，这个方向接近，但更准确的说法是：

- `service` 会把查询结果组装成 `RunListResponse`
- `router` 直接 return
- FastAPI 再按 `response_model` 做响应约束和序列化

也就是说，这里不是“最后临时拿 schema 校验一下”，而是 schema 本来就在返回链路里。

##### 最优答案

`GET /api/runs` 进来后，先由 `router` 接住请求；`router` 不自己查库，而是把查询动作交给 `service`；`service` 再调用 `repository` 的列表查询方法；`repository` 从 `SQLite` 的 `runs` 表里把记录查出来，并按 `created_at` 倒序返回；然后 `service` 把这些记录组装成 `RunListResponse(items=[...])`；最后由 `router` 返回给调用方。

最关键的一句是：

```text
GET /api/runs 一定要查 SQLite，因为当前 run 列表的真实数据来源就是 runs 表。
```

#### 题目 2

假设现在产品说列表页还想展示“总条数”，但暂时不做分页。你觉得最适合先改哪一层、怎么改，为什么当前用 `items` 包一层会比直接返回裸数组更稳？

##### 你的答案

<你填写> 我觉得应该是services层，再次处理下repository返回的查询records结果，将总条数这个信息也体现出来

##### 我的 Review

你答到一个关键点了：`service` 的确是很适合补“总条数”这类业务响应信息的地方。

但这题还不够完整，主要少了两点：

1. 不只是 `service`，还要先改响应 schema

因为现在的返回结构只有：

```json
{
  "items": [...]
}
```

如果要加总条数，首先就要把 schema 扩成例如：

```json
{
  "items": [...],
  "total": 2
}
```

2. 你没有回答“为什么 `items` 包一层比裸数组更稳”

这题的重点其实就在这里：

- 如果现在直接返回裸数组，后面再加 `total`，接口结构就得整体改掉
- 现在先包成对象，后续扩字段就自然很多

所以这题后面要习惯同时回答：

- 该改哪层
- 为什么这个结构设计对后续更稳


##### 最优答案

如果列表页要加“总条数”，最合适的做法是先改 `schema` 和 `service`：

- `schema`：把 `RunListResponse` 从只有 `items`，扩成包含 `items` 和 `total`
- `service`：在拿到 `records` 后，继续组装出 `total=len(records)`
- `router`：通常不用改，只要继续 `return get_run_list()`

当前用 `items` 包一层比直接返回裸数组更稳，因为后面如果想继续加：

- `total`
- 分页信息
- 筛选条件回显

都可以直接在响应对象上扩字段，而不用把整个接口从“数组”改成“对象”。

#### 题目 3

如果有人为了省事，打算在 `router` 里直接写一份假的 run 列表返回，不去查数据库。你觉得这会带来什么问题？请从“业务可信度”和“后续扩展”两个角度各说一点。

##### 你的答案

<你填写> 那数据都是假的 还有什么可信度

##### 我的 Review

这题你只回答到了“业务可信度”这一半，而且还是比较口语化的版本，方向没错，但还不够支撑后续设计判断。

这题要同时从两个角度回答：

1. 业务可信度

如果 `router` 直接返回假列表，那前端看到的数据就和数据库里的真实 run 记录无关，调用方无法相信这个列表真的代表平台当前状态。

2. 后续扩展

后面你还要继续做：

- `GET /api/runs/{run_id}`
- Jenkins 回写状态
- 列表筛选 / 分页 / 排序

如果列表一开始就是假数据，后面这些能力都会被迫重写，当前这条链路也没有真实复用价值。

##### 最优答案

如果在 `router` 里直接写一份假的 run 列表返回，不去查数据库，会有两个明显问题。

第一，业务可信度会出问题。

因为前端看到的列表不再来自 `runs` 表的真实记录，而只是接口层手写的假数据。这样调用方看到“有 run”并不代表平台里真的存在这些 run。

第二，后续扩展会很差。

因为后面无论是：

- `GET /api/runs/{run_id}`
- 状态更新展示
- 筛选、分页、排序

都必须建立在真实数据查询之上。如果现在先偷懒写假数据，后面这些能力基本都要重做，当前代码也没有长期价值。

---

## Step 9：实现 `GET /api/runs/{run_id}`，把单条 run 详情查出来

### 这一步要解决什么问题

前一步已经能通过 `GET /api/runs` 查到 run 列表，但列表只能告诉我们“现在有哪些 run”。

还缺一个非常关键的能力：

- 已知某个 `run_id`
- 平台要能查出这条 run 的单条详情

如果这一步不补，后面很多东西都接不上：

1. 前端详情页没有数据来源
2. Jenkins 回写后，调用方没法按 `run_id` 精确查看这一条记录
3. 后续 artifact、KPI、状态变化都缺少稳定详情入口

所以这一步的目标很明确：

- 新增 `GET /api/runs/{run_id}`
- 能按 `run_id` 从 `SQLite` 查询单条记录
- 查不到时返回 `404`

### 代码示例

```python
# app/repositories/run_repository.py
def get_run_record_by_id(run_id: str) -> dict[str, str] | None:
    initialize_run_repository()

    with sqlite3.connect(settings.runs_db_path) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            """
            SELECT
                run_id,
                testline,
                robotcase_path,
                status,
                message,
                created_at,
                updated_at
            FROM runs
            WHERE run_id = ?
            """,
            (run_id,),
        ).fetchone()

    return dict(row) if row else None
```

```python
# app/services/run_service.py
def get_run_detail(run_id: str) -> RunDetailResponse:
    record = get_run_record_by_id(run_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Run not found.")

    return RunDetailResponse(**record)
```

```python
# app/api/v1/router.py
@router.get("/runs/{run_id}", response_model=RunDetailResponse, tags=["run"])
def get_run(run_id: str) -> RunDetailResponse:
    return get_run_detail(run_id)
```

### 函数调用流程图（含大概意思）

```text
调用方发起 GET /api/runs/{run_id}
   |
   | 请求先进入 router
   v
get_run(run_id)
   |
   | router 把 run_id 交给 service
   v
get_run_detail(run_id)
   |
   | service 调 repository 查单条记录
   | 查不到就抛 404
   | 查到了就组装详情 schema
   v
get_run_record_by_id(run_id)
   |
   | repository 从 SQLite 的 runs 表里按 run_id 查询
   v
RunDetailResponse -> JSON
```

### 相关问题记录

#### 问题 1：为什么已经有列表接口了，还要单独做详情接口？

因为列表接口和详情接口的职责不一样。

列表接口重点是：

- 快速看到有哪些 run
- 适合做列表页展示

详情接口重点是：

- 已知某个 `run_id`
- 精确查询这一条 run 的完整信息

后面只要进入“点进某条 run 看详情”的场景，详情接口就不可少。

#### 问题 2：为什么查不到时要返回 `404`，而不是返回一个空对象？

因为“没有这条 run”本质上是资源不存在，不是“字段暂时为空”。

如果返回空对象，会让调用方分不清：

- 是真的没查到
- 还是接口返回结构有问题

而 `404` 的语义会更清晰：

```text
这个 run_id 对应的资源不存在。
```

#### 问题 3：为什么这一步的详情字段先和列表项保持一致？

因为当前阶段的重点是先把“按 ID 精确查到单条记录”这条链路打通。

现在数据库里已经有的核心字段就是：

- `run_id`
- `testline`
- `robotcase_path`
- `status`
- `message`
- `created_at`
- `updated_at`

所以第一版详情接口先返回这批字段最稳。

后面如果接 Jenkins、artifact、KPI，再继续扩详情结构就行。

### 测试关注点

这一小步开始，除了功能是否打通，还要重点盯 3 类测试点：

1. 查询命中路径

- 已存在的 `run_id` 能否返回正确详情
- 返回字段是否与数据库记录一致

2. 查询未命中路径

- 不存在的 `run_id` 是否明确返回 `404`
- 错误消息是否稳定

3. 接口职责边界

- `router` 是否只负责接收 path 参数并转交 service
- `service` 是否负责“查到/查不到”的业务语义
- `repository` 是否只负责查数据库

### 建议补的测试场景

- 正常场景：先创建一条 run，再用它的 `run_id` 查详情
- 异常场景：查一个不存在的 `run_id`，确认返回 `404`
- 一致性场景：列表接口看到的某条 run，详情接口按同一个 `run_id` 也能查到
- 边界场景：后续如果 `run_id` 格式扩展，详情查询不应该依赖固定后缀模式

### AI 可辅助的测试动作

- 帮你列出“详情接口最容易漏掉的失败场景”
- 帮你检查当前 pytest 是否只覆盖成功路径
- 帮你补一份“列表接口与详情接口的一致性测试点清单”

### 测试工程补充：为什么这一步开始引入 fixture 和 Allure

这一轮除了补详情接口，我还顺手把测试工程结构往前推了一步：

- 用 `tests/conftest.py` 收敛公共 fixture
- 用 `allure-pytest` 给测试补基础报告能力

这样做的原因是：

1. 现在测试文件里已经开始出现重复准备动作

例如：

- 切换测试用数据库路径
- 创建 `TestClient`
- 先创建一条 run 再做后续查询

这些逻辑如果每个测试都各写一遍，后面测试一多会越来越乱。

所以这一轮开始，适合收成 fixture：

- `isolated_runs_db`
- `client`
- `db_connection`
- `create_run_via_api`

2. 从测试工程角度，fixture 更适合测试工程师长期维护

因为它能把：

- 环境准备
- 公共前置动作
- 测试数据创建

从单个测试用例里抽出去，让每条测试更专注于“我要验证什么”。

3. Allure 适合后面逐步接 Jenkins 报告

当前先不把 Allure 用得很重，只先做两件事：

- 安装 `allure-pytest`
- 给测试加基础 `feature / story / title`

这样后面你在服务器或 Jenkins 上执行：

```bash
python -m pytest tests --alluredir=allure-results
```

就已经能产出结构化测试结果文件，为后续报告展示做准备。

要注意：

```text
allure-pytest 负责生成结果文件；
真正把结果渲染成 HTML 报告，还需要 Allure CLI 或 Jenkins 侧的 Allure 能力。
```

### 测试工程补充：当前 `platform-api` 的 API 测试分层怎么理解

你现在是测试工程师视角来推进这个项目，所以这里很适合先把“当前阶段到底该怎么分层测”固定下来。

在 `platform-api` 现在这个阶段，最适合先按 3 层来理解：

#### 第 1 层：API 契约层

这一层最关心的是：

- 请求打进来后状态码对不对
- 返回 JSON 结构对不对
- 必填字段有没有
- 查不到时错误语义对不对

这一层最典型的工具就是：

- `TestClient`

例如现在这些测试，本质上都属于 API 契约层：

- `GET /api/health`
- `POST /api/runs`
- `GET /api/runs`
- `GET /api/runs/{run_id}`

你可以把这一层理解成：

```text
先确认接口“说话说得对不对”。
```

#### 第 2 层：持久化验证层

这一层关心的不只是接口回了什么，而是：

```text
接口动作之后，数据库里到底有没有真的变成预期状态。
```

例如：

- 创建 run 后，`runs` 表里是不是真的多了一条记录
- 查详情时，返回内容是不是和库里的记录一致

这一层现在可以借助：

- `db_connection` fixture

你可以把这一层理解成：

```text
不光要看接口“嘴上怎么说”，还要看数据库“实际上怎么记”。
```

#### 第 3 层：系统 / 集成层

这一层是更后面的事情，重点是：

- FastAPI 和 Jenkins 怎么交互
- Jenkins 和 Agent / Robot 怎么交互
- 状态、产物、回写、前端展示是否一致

这一层当前还不需要做重，但你要先知道它会存在。

也就是说，后面这个项目最终测试不会只停留在 `pytest + TestClient`，还会继续往：

- 服务器验证
- Jenkins 流水线验证
- 端到端链路验证

扩展。

#### 为什么现在最适合先用前两层？

因为当前代码规模还不大，最关键的是先把最小接口闭环打稳。

所以当前更推荐的顺序是：

1. 先用 API 契约层确认接口行为对不对
2. 再用少量持久化验证层确认不是“假接口”
3. 等接 Jenkins 后，再逐步补系统 / 集成层

你可以先强行记成一句话：

```text
先测接口会不会说，再测数据库有没有记，最后再测系统是不是整条链路都通。
```

#### 为什么这次也把 `health` 迁到 fixture 风格？

因为后面我们希望测试风格尽量统一。

虽然 `health` 很简单，它并不依赖复杂持久化逻辑，但把它也写成：

- `TestClient`
- API 调用
- Allure 标注

会带来两个好处：

1. 后面你看测试文件时，风格更统一
2. 你能更自然地把“接口测试”当成一个整体来看，而不是一部分测 service，一部分测 API

所以现在的取舍是：

- `health` 继续保持简单
- 但测试风格向 API 层统一靠拢

### 如何验证

先在 Jenkins Master / 目标服务器执行：

```bash
cd /path/to/jenkins_robotframework/platform-api
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests/test_health.py tests/test_runs.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

如果想同时产出 Allure 结果文件，可改成：

```bash
python -m pytest tests/test_health.py tests/test_runs.py --alluredir=allure-results
```

另开一个终端验证：

```bash
RUN_ID=$(curl -X POST http://127.0.0.1:8000/api/runs \
  -H "Content-Type: application/json" \
  -d '{"testline":"smoke","robotcase_path":"cases/login.robot"}' | python -c "import sys, json; print(json.load(sys.stdin)['run_id'])")

curl http://127.0.0.1:8000/api/runs/$RUN_ID
curl http://127.0.0.1:8000/api/runs/run-not-found
```

如果在 Windows 本地验证，可用：

```powershell
cd C:\TA\jenkins_robotframework\platform-api
python -m pytest tests/test_health.py tests/test_runs.py
```

### 验收结果

- [x] `GET /api/runs/{run_id}` 已经落地
- [x] 详情接口会真正从 `SQLite` 的 `runs` 表按 `run_id` 查询
- [x] 查不到记录时会返回 `404`
- [x] 已有测试覆盖“查到”和“查不到”两条主路径
- [x] 测试公共准备逻辑已经开始收敛到 fixture
- [x] 项目已具备生成 Allure 结果文件的基础能力

### 我这一步学到了什么

- 列表接口解决“有哪些”，详情接口解决“这一条到底是什么”
- 资源不存在时，优先用 `404` 表达，而不是返回模糊的空对象
- 从测试角度看，详情接口至少要同时覆盖命中路径和未命中路径
- 从测试工程角度看，fixture 适合抽公共准备逻辑，Allure 适合逐步把结果沉淀成可展示报告

### 复盘问题（你来回答）

#### 题目 1

请你用自己的话复述一下 `GET /api/runs/{run_id}` 这条链路，并重点说明：为什么这一步的核心不是“再查一遍列表”，而是“按 ID 精确查询单条记录”？

##### 你的答案

<你填写>

##### 我的 Review

<我来补 review 结果>

##### 最优答案

<我来补最终沉淀版答案>

#### 题目 2

假设现在测试要补一个“详情接口”的最小用例集，你觉得最少应该包含哪两类测试？每一类主要在验证什么？

##### 你的答案

<你填写>

##### 我的 Review

<我来补 review 结果>

##### 最优答案

<我来补最终沉淀版答案>

#### 题目 3

如果有人为了省事，打算让 `GET /api/runs/{run_id}` 查不到时直接返回 `200 + {}`，你觉得这样会带来什么问题？请从“接口语义”和“测试判断”两个角度各说一点。

##### 你的答案

<你填写>

##### 我的 Review

<我来补 review 结果>

##### 最优答案

<我来补最终沉淀版答案>

---

## 后续记录模板

后面每一步统一按这个格式追加：

```markdown
## Step N：<标题>

### 这一步要解决什么问题

<说明>

### 代码示例

```python
# 或 txt / json
```

### 函数调用流程图（含大概意思）

```text
函数 A / 请求入口
   |
   | 先做什么
   v
函数 B / service / schema
   |
   | 再做什么
   v
函数 C / 返回结果
```

在这个小节里默认只说明：

- 谁先调用谁
- 每层大概负责什么
- 输入从哪里进来
- 输出最后怎么返回

具体某一行语法如果你练习时看不懂，再单独提问，我把问答补到“相关问题记录”。

### 相关问题记录

- 记录这一小步里额外问到的概念问题
- 用简短问答的形式补充

### 测试关注点

- <这一小步最值得测试的接口契约 / 边界值 / 失败路径 / 分层职责>

### 建议补的测试场景

- <成功路径>
- <失败路径>
- <一致性 / 边界 / 风险路径>

### AI 可辅助的测试动作

- <AI 可以帮忙补什么测试点、检查什么漏测、生成什么测试骨架>

### 涉及文件

- `path/to/file`

### 你自己动手时的落代码顺序

1. ...
2. ...

### 如何验证

```powershell
# 优先写 Jenkins Master / 构建机 / 服务器上的验证命令
# 如果本地也能做，再补一个“可选本地验证”
```

### 验收结果

- [ ] 条件 1
- [ ] 条件 2

### 我这一步学到了什么

- <总结 1>
- <总结 2>

### 复盘问题（你来回答）

#### 题目 1

<调用链复述题：请你用自己的话讲清这一步的业务流程和调用链>

##### 你的答案

<你填写>

##### 我的 Review

<我来补 review 结果>

##### 最优答案

<我来补最终沉淀版答案>

#### 题目 2

<测试设计题 / 场景题：给一个真实改动场景，请说明应该补哪类测试、改哪一层、为什么这样拆>

##### 你的答案

<你填写>

##### 我的 Review

<我来补 review 结果>

##### 最优答案

<我来补最终沉淀版答案>

#### 题目 3

<风险题 / AI 扩展题：说明当前设计为什么这样做，不这样做会有什么问题，或 AI 可以帮你补什么测试思路>

##### 你的答案

<你填写>

##### 我的 Review

<我来补 review 结果>

##### 最优答案

<我来补最终沉淀版答案>
```
