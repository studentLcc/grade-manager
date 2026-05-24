# Grade Manager

Grade Manager 是一个面向教师的成绩与班级管理系统，覆盖班级学生档案、课程课表、考试编排、成绩录入、Excel 导入、统计分析和工作台概览等常见教学管理流程。项目采用前后端分离架构，适合作为学校成绩管理场景的开源参考实现，也可以作为二次开发基础。

## 功能特性

- 教师账号注册、登录与 JWT 认证
- 班级、学生、课程、课表基础数据管理
- 考试创建、班级快照、科目配置与成绩表生成
- 成绩录入、成绩状态管理、Excel 导入与导入记录追踪
- 考试统计、分数段、排名、异常成绩与缺失成绩分析
- 工作台概览：今日课表、近期考试、成绩概览、班级均分趋势
- MySQL 持久化、Alembic 数据库迁移、可选演示数据生成

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | Vue 3、TypeScript、Vite、Element Plus、Pinia、Vue Router |
| 后端 | FastAPI、SQLAlchemy 2、Pydantic、Alembic |
| 数据库 | MySQL 8.4 |
| 测试 | Pytest、Vitest、Vue Test Utils、Playwright |
| 工具 | uv、npm、Docker Compose、ESLint、Ruff |

## 项目结构

```text
grade-manager/
├── backend/              # FastAPI API、SQLAlchemy 模型、迁移与测试
│   ├── app/
│   ├── alembic/
│   ├── scripts/
│   └── tests/
├── frontend/             # Vue 3 应用与前端测试
│   ├── src/
│   ├── tests/
│   └── e2e/
├── scripts/dev.sh        # 本地开发辅助脚本
├── docker-compose.yml    # 本地 MySQL 服务
└── README.md
```

## 环境要求

- Docker 和 Docker Compose
- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- npm

## 快速开始

推荐使用本地开发脚本。它会启动 MySQL，根据 `backend/.env.example` 创建 `backend/.env`，安装依赖并执行数据库迁移。

```bash
./scripts/dev.sh init
./scripts/dev.sh start
```

启动后访问：

- 前端：`http://127.0.0.1:5173`
- API 文档：`http://127.0.0.1:8000/docs`
- API 基础地址：`http://127.0.0.1:8000/api/v1`

常用脚本命令：

```bash
./scripts/dev.sh status
./scripts/dev.sh logs
./scripts/dev.sh restart
./scripts/dev.sh stop
./scripts/dev.sh stop --mysql
```

`scripts/dev.sh` 是 Bash 脚本。Windows 用户可以使用 Git Bash、WSL，或参考下面的手动启动方式。

## 手动启动

启动 MySQL：

```bash
docker compose up -d mysql
```

启动后端：

```bash
cd backend
cp .env.example .env
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

另开一个终端启动前端：

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev -- --host 127.0.0.1
```

PowerShell 写法：

```powershell
cd frontend
$env:VITE_API_BASE_URL = "http://127.0.0.1:8000/api/v1"
npm run dev -- --host 127.0.0.1
```

## 账号与演示数据

系统不会自动创建默认管理员账号。首次使用时可以在注册页创建教师账号，也可以直接调用注册接口：

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"teacher1","password":"strong-password","display_name":"王老师"}'
```

如果希望本地工作台有更完整的演示数据，可以生成演示班级、学生、课程、课表、考试和成绩：

```bash
cd backend
uv run python -m scripts.seed_demo_data
```

默认演示账号：

- 用户名：`teacher1`
- 密码：`strong-password`

演示数据命令对同一组配置是幂等的，开发时可以重复执行。

## 配置说明

后端配置读取自 `backend/.env`。

| 变量 | 示例 | 说明 |
| --- | --- | --- |
| `DATABASE_URL` | `mysql+pymysql://grade_manager:grade_manager@127.0.0.1:3306/grade_manager` | SQLAlchemy 数据库连接地址 |
| `SECRET_KEY` | `change-me-in-local-env` | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_DAYS` | `30` | 登录令牌有效天数 |
| `APP_TIMEZONE` | `Asia/Shanghai` | 应用时区 |
| `BACKEND_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | 允许访问后端的前端源 |

前端通过 `VITE_API_BASE_URL` 指定后端 API 地址。

## 测试与质量检查

后端：

```bash
cd backend
uv run pytest -v
uv run ruff check .
```

前端：

```bash
cd frontend
npm run test
npm run build
npm run lint
npm run test:e2e
```

Playwright E2E 测试需要本地安装对应浏览器依赖。

## API 概览

所有 API 路由都挂载在 `/api/v1` 下。

- `/auth`：认证
- `/classes`、`/students`、`/courses`、`/schedules`：基础数据管理
- `/exams`：考试配置与成绩表
- `/scores`：成绩查询、编辑与导入
- `/imports`：导入批次详情
- `/statistics`：成绩统计分析
- `/dashboard`：工作台汇总与趋势

后端运行后，可以通过 `http://127.0.0.1:8000/docs` 查看交互式 OpenAPI 文档。

## 贡献指南

1. 基于最新主分支创建功能分支。
2. 保持变更聚焦，并为关键行为补充测试。
3. 提交前运行后端和前端验证命令。
4. 如果包含可见 UI 改动，请在 PR 中附上截图或说明。

## 许可证

本项目使用 Apache License 2.0，详见 [LICENSE](LICENSE)。
