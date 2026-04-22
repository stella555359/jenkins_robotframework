# platform-api

`platform-api` 是当前轻量化自动化平台的 FastAPI 后端。

第一轮先从最小骨架开始，只打通：

- `GET /api/health`
- `POST /api/runs`

后续再逐步扩展：

- `GET /api/runs`
- `GET /api/runs/{run_id}`
- Jenkins 集成
- 更完整的 SQLite 持久化

当前 `POST /api/runs` 已经会把最小 run 元数据写入 `SQLite`，默认数据库路径为：

- `data/results/automation_platform.db`

如需覆盖默认值，可在 `.env` 中设置：

- `RUNS_DB_PATH`
