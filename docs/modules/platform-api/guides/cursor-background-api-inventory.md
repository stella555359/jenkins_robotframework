# Cursor 可后台调用的 API 清单

## 结论

Cursor **没有**单独的「聊天补全 API」或「纯 LLM 推理 API」。后台可调用的能力都围绕 **Agent（智能体）** 模型：创建 Agent → 发送 prompt → 轮询/流式获取 Run 结果。

对 Jenkins log AI 分析场景：

- **首选**：Cloud Agent no-repo（`POST /v1/agents` 不传 `repos`）—— 纯 HTTP，适合服务器 worker
- **已验证可用**：`GET /v1/models` —— 服务器 TypeScript + ProxyAgent 已通过
- **当前阻塞**：`POST /v1/agents` —— 403 `feature_unavailable`（账号/Cloud Agents 权限）

本项目 worker 已改为 **REST 直调**（`platform-api/app/services/cursor_rest_client.py`），不再依赖 Python `cursor-sdk`。

## 三种调用方式

| 方式 | 包/地址 | 适合场景 |
|------|---------|----------|
| REST API | `https://api.cursor.com/v1/*` | 任意语言、CI、Python worker |
| TypeScript SDK | `@cursor/sdk` | Node sidecar、手工 smoke |
| Python SDK | `cursor-sdk` | 当前不推荐（Linux/Windows 均不稳定） |

认证：`CURSOR_API_KEY`（User API Key 或 Team Service Account Key）。Team Admin API Key **尚不支持**。

官方文档：

- [Cloud Agents REST API](https://cursor.com/docs/cloud-agent/api/endpoints)
- [TypeScript SDK](https://cursor.com/docs/sdk/typescript)
- [Python SDK](https://cursor.com/docs/sdk/python)

## REST API 清单

### 元数据 / 鉴权探测

| 方法 | 路径 | 用途 |
|------|------|------|
| GET | `/v1/me` | 验证 API Key 归属 |
| GET | `/v1/models` | 列出可用模型 |
| GET | `/v1/repositories` | GitHub App 可访问仓库（限流 1/min） |

### Cloud Agent 核心

| 方法 | 路径 | 用途 |
|------|------|------|
| POST | `/v1/agents` | 创建 Agent 并 enqueue 首次 Run |
| GET | `/v1/agents` | 列出 Agent |
| GET | `/v1/agents/{id}` | 查询 Agent |
| POST | `/v1/agents/{id}/runs` | 追加 prompt |
| GET | `/v1/agents/{id}/runs/{runId}` | 获取 Run 结果 |
| GET | `/v1/agents/{id}/runs/{runId}/stream` | SSE 流式事件 |
| POST | `/v1/agents/{id}/runs/{runId}/cancel` | 取消 Run |

no-repo 创建示例（最适合 log 分析，不依赖 GitHub 默认分支）：

```bash
curl -X POST https://api.cursor.com/v1/agents \
  -u "$CURSOR_API_KEY:" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": { "text": "分析以下 Jenkins log，输出 JSON..." },
    "model": { "id": "composer-2.5" }
  }'
```

### Self-hosted Worker（仅私有 worker pool）

| 方法 | 路径 |
|------|------|
| POST | `/v1/sub-tokens` |
| GET | `/v1/workers` |
| GET | `/v1/fleet` |

## 不能后台调用的部分

- Cursor IDE 界面（编辑器、Chat、Composer UI）
- Dashboard 设置（API Key、GitHub App、环境配置）
- 裸 LLM chat/completions 端点
- MCP OAuth 登录（需浏览器）

## 项目内 smoke 脚本

```bash
cd platform-api
source .venv/bin/activate
export CURSOR_API_KEY="crsr_..."
export HTTPS_PROXY=http://10.144.1.10:8080   # 如需要
python scripts/cursor_api_smoke.py
```

脚本顺序：

1. `GET /v1/me`
2. `GET /v1/models`
3. `POST /v1/agents` no-repo + 轮询 run

## 403 feature_unavailable 排查与联系支持

若 smoke 第 3 步返回 403，通常表示 **Cloud Agents 功能未对当前账号开通**，与 Windows/Linux 无关。

自查清单：

1. Dashboard → API Keys：确认是 **User API Key**，不是 Team Admin API Key
2. Dashboard → Cloud Agents：能否手动创建任务
3. GitHub App 是否已安装（仅 cloud+repo 场景需要；no-repo 不需要）
4. 换账号或联系 Cursor 支持开通 Cloud Agents beta

联系支持时建议提供：

- API Key 前缀（不要发完整 key）
- `GET /v1/me` 返回的 `userEmail` / `apiKeyName`
- `POST /v1/agents` 的 HTTP 状态码与 `code` 字段（如 `feature_unavailable`）
- Dashboard 手动创建 Cloud Agent 是否也失败（如 `Could not resolve default branch`）

支持入口：[Cursor Support](https://cursor.com/support) 或 Dashboard 内 Help。

在权限恢复前，生产默认路径仍为 `rules_first`。

## Worker 集成路径（已选型）

**方案 A：REST 直调（已采用）**

- 模块：`platform-api/app/services/cursor_rest_client.py`
- Worker：`ai_analysis_worker._invoke_cursor_rest()`
- 优点：纯 Python stdlib、可走 HTTP 代理、不依赖 cursor-sdk bridge

**方案 B：Node sidecar + TypeScript SDK（备选）**

- 仅在 REST 仍不足时考虑
- `Cursor.models.list` 已验证；`Agent.prompt` cloud 仍受同一 403 限制

## 配置项

| 环境变量 / 配置 | 默认值 | 说明 |
|----------------|--------|------|
| `CURSOR_API_KEY` | — | 必填 |
| `HTTPS_PROXY` / `HTTP_PROXY` | — | 服务器代理 |
| `cursor_api_base_url` | `https://api.cursor.com` | API 根地址 |
| `cursor_api_run_timeout_seconds` | `600` | Run 轮询总超时 |
| `cursor_api_poll_seconds` | `5` | 轮询间隔 |
| `ai_analysis_model` | `auto` | 模型 ID，`auto` 时省略 model 字段 |

## 验证命令（服务器）

```bash
cd /opt/jenkins_robotframework/platform-api
source .venv/bin/activate
export CURSOR_API_KEY="crsr_..."
export HTTPS_PROXY=http://10.144.1.10:8080
export HTTPS_PROXY=$HTTPS_PROXY
python scripts/cursor_api_smoke.py
```

预期：

- 第 1、2 步成功 → Key 与基础 API 可用
- 第 3 步若 403 → 按上文联系 Cursor 支持
- 第 3 步若 FINISHED → worker 可切 `analysis_mode=cursor_sdk`（名称保留，实现为 REST）
