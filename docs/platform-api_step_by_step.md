# Platform API 手把手实现记录
## FastAPI 从零开始的分步实践

**文档目的**：

- 记录 `platform-api` 从最小骨架到可用后端的完整实现过程
- 每一步都说明“为什么做、做了什么、怎么验证、学到了什么”
- 让后续实现过程可以回看，而不是只留在聊天记录里

---

## 当前约定

这份记录统一采用下面的方法推进：

1. 先讲这一步要解决什么问题
2. 先把本 step 的代码示例写进本文档
3. 对示例代码做逐行解释
4. 再给出你自己落代码时的执行顺序
5. 最后再写验证步骤，但默认按“服务器 / Jenkins Master / 构建机可执行”来设计

也就是说，这份文档不是“大而全设计文档”，而是“边做边学的实现日志”。

以后默认采用下面这个协作方式：

- 我先在本文档里给出示例代码
- 我再逐行解释每一段代码是什么意思
- 你确认理解后，再自己把代码写进 `platform-api/` 源码目录
- 除非你明确要求我直接落代码，否则后续步骤我不再默认直接改源码

### 验证方式约定

考虑到你的本机开发环境受限，后续所有 step 默认按下面的方式写验证步骤：

1. `IDE` 负责写代码和看文档
2. `GitHub / Git` 负责同步代码
3. `Jenkins Master`、构建机或目标服务器负责安装依赖、启动服务、跑测试、做联调验证

也就是说：

- 本地验证不是默认前提
- 如果某一步需要 `Node.js`、Python 依赖、构建命令、服务启动命令，我会优先写成“在 Jenkins Master / 构建机 / 服务器上怎么验证”
- 本地能做的验证，只作为“可选补充”

后面你看到“如何验证”时，优先按服务器侧执行，不再假设你本机能随便安装软件。

---

## 学习目标

当前阶段的目标不是一次性把 `platform-api` 全写完，而是按最小闭环逐步实现：

1. 补最小目录结构
2. 写 `GET /api/health`
3. 写最小 schema
4. 写 `POST /api/runs`
5. 接入 SQLite
6. 保存 run
7. 查询 run 列表
8. 查询 run 详情
9. 最后再接 Jenkins

---

## 进度看板

- [x] 第 1 步：补最小目录结构
- [x] 第 2 步：实现 `GET /api/health`
- [x] 第 3 步：加入基础配置层
- [ ] 第 4 步：加入 run 相关 schema
- [ ] 第 5 步：实现 `POST /api/runs`
- [ ] 第 6 步：接入 SQLite
- [ ] 第 7 步：实现 run 持久化
- [ ] 第 8 步：实现 `GET /api/runs`
- [ ] 第 9 步：实现 `GET /api/runs/{run_id}`
- [ ] 第 10 步：准备 Jenkins 集成

---

## Step 0：开始前说明

### 这一步要解决什么问题

先建立一份专门的过程记录文档，把后续 `platform-api` 的实现步骤单独沉淀下来。

### 这一步做了什么

- 创建了 `docs/platform-api_step_by_step.md`
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

#### 方式 A：推荐做法（服务器 / Jenkins Master 验证）

先把代码同步到服务器对应目录，然后执行：

```powershell
cd C:\TA\jenkins_robotframework\platform-api
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest tests/test_health.py
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

另开一个终端窗口验证：

```powershell
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

### 逐行解释

1. ...
2. ...

### 相关问题记录

- 记录这一小步里额外问到的概念问题
- 用简短问答的形式补充

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
```
