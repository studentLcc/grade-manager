# Grade Manager

Teacher grade management system with FastAPI backend and Vue 3 frontend.

## Development

```bash
docker compose up -d mysql
cp .env.example .env
printf '\nBACKEND_CORS_ORIGINS=http://127.0.0.1:5173\n' >> .env
cd backend
uv sync --extra dev
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev -- --host 127.0.0.1
```

## Verification

```bash
(cd backend && uv run pytest -v)
(cd frontend && npm run test && npm run build)
(cd frontend && npm run lint)
(cd frontend && npm run test:e2e)
```

Playwright E2E tests require the Playwright browser and Linux system dependencies.
