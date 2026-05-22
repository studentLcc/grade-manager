# Grade Manager

教师成绩管理系统，后端使用 FastAPI，前端使用 Vue 3。

## Prerequisites

- Docker / Docker Compose
- Python 3.12 和 `uv`
- Node.js 20+ 和 npm

## First-Time Setup

推荐使用一键初始化：

```bash
./scripts/dev.sh init
```

它会启动 MySQL、生成 `backend/.env`、安装后端和前端依赖，并执行数据库迁移。

也可以手动初始化：

```bash
docker compose up -d mysql
test -f backend/.env || cp backend/.env.example backend/.env
(cd backend && uv sync --extra dev)
(cd backend && uv run alembic upgrade head)
(cd frontend && npm install)
```

系统不会自动创建内置默认账号。首次启动后，在注册页创建教师账号；如果需要示例账号，可以在后端启动后执行本文后面的初始化账号命令。

## Start The App

推荐使用一键脚本启动开发环境：

```bash
./scripts/dev.sh init
./scripts/dev.sh start
```

常用命令：

```bash
./scripts/dev.sh status
./scripts/dev.sh logs
./scripts/dev.sh restart
./scripts/dev.sh stop
./scripts/dev.sh stop --mysql
```

脚本会把后端和前端放到后台运行，PID 和日志写入 `.run/`。默认 `stop` 只停止后端和前端；如果也要停止 MySQL 容器，使用 `stop --mysql`。

也可以手动启动各服务：

启动 MySQL：

```bash
docker compose up -d mysql
```

启动后端：

```bash
(cd backend && uv run alembic upgrade head)
(cd backend && uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000)
```

后端启动后，可另开一个终端创建示例账号：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"teacher1","password":"strong-password","display_name":"王老师"}'
```

示例登录账号：

- 用户名：`teacher1`
- 密码：`strong-password`

如果已经通过页面注册了自己的账号，直接使用自己的用户名和密码登录。重复创建同名账号会返回用户名冲突。

启动前端：

```bash
(cd frontend && VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev -- --host 127.0.0.1)
```

访问地址：

- 前端：`http://127.0.0.1:5173`
- 后端 API：`http://127.0.0.1:8000/api/v1`
- API 文档：`http://127.0.0.1:8000/docs`

## Verification

```bash
(cd backend && uv run pytest -v)
(cd frontend && npm run test && npm run build)
(cd frontend && npm run lint)
(cd frontend && npm run test:e2e)
```

Playwright E2E tests require the Playwright browser and Linux system dependencies.
