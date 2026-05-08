# Step 1：Robot Portal B1 MVP

## 目标

实现最小 Portal 页面，让用户用一个 **Run** 按钮跑真实 Robot case。前端内部采用 B1：

```text
POST /api/runs
POST /api/runs/{run_id}/trigger
navigate /runs/{run_id}
```

## 本步新增

- `automation-portal/package.json`：Vite React TypeScript 工程脚本。
- `automation-portal/src/api.ts`：封装 platform-api 调用。
- `automation-portal/src/pages/RobotRunForm.tsx`：Robot run 表单，一键 create + trigger。
- `automation-portal/src/pages/RunList.tsx`：run 列表。
- `automation-portal/src/pages/RunDetail.tsx`：run 状态、Jenkins ref、artifact、KPI summary、metadata 展示，并在 `created` / `trigger_failed` 时提供 Retry Trigger。
- `automation-portal/src/styles.css`：MVP 样式。

## 页面路由

```text
/runs/new      Robot run form
/runs          Run list
/runs/:runId   Run detail
```

## 前端字段映射

表单会创建 `executor_type="robot"` 的 run：

```json
{
  "testline": "T813",
  "robotcase_path": "testsuite/Hangzhou/RRM/example.robot",
  "executor_type": "robot",
  "build": "optional",
  "metadata": {
    "case_name": "optional",
    "selected_tests": ["one per line"],
    "robot_variables": {}
  }
}
```

trigger 失败时，后端会把 run 写成 `trigger_failed`；前端仍会跳到 detail 页面，用户可以点 **Retry Trigger**。

## 本地验证

```powershell
cd C:\TA\jenkins_robotframework\automation-portal
npm install
npm run build
npm run dev
```

默认 `.env.example`：

```text
VITE_APP_TITLE=Automation Portal
VITE_API_BASE_URL=/api
```

Vite dev server 会把 `/api` proxy 到 `http://127.0.0.1:8000`。
