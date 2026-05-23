# Grade Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first version of the teacher grade management system described by `docs/superpowers/specs/2026-05-20-grade-manager-design.md` and `docs/superpowers/specs/2026-05-21-grade-manager-frontend-workflow-design.md`.

**Architecture:** The backend is a FastAPI application under `/api/v1`, with SQLAlchemy 2.x ORM models, Alembic migrations, Pydantic schemas, JWT authentication, teacher-scoped services, Excel import services, statistics services, and thin routers. The frontend is a Vue 3 + Vite + Element Plus desktop-first management app with Pinia auth/session state, Vue Router protected routes, Axios interceptors, exam-driven score workflows, and compact dashboard visual constraints. Backend tests drive business rules first; frontend tests and Playwright checks verify workflow and layout behavior.

**Tech Stack:** Python 3.12, uv, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, PyMySQL, python-jose, passlib, openpyxl, pytest, Vue 3, TypeScript, Vite, Element Plus, Pinia, Vue Router, Axios, Vitest, Playwright, MySQL 8.

---

## Source Documents

- System design: `docs/superpowers/specs/2026-05-20-grade-manager-design.md`
- Frontend workflow design: `docs/superpowers/specs/2026-05-21-grade-manager-frontend-workflow-design.md`
- Visual baseline artifact: `.superpowers/brainstorm/32672-1779371349/content/frontend-workflow-preview-compact-v5.html`

## Scope Boundary

This is a master implementation plan because the repository currently has design documents but no application source. The plan is split into independently reviewable increments. Each task ends with a working state, verification commands, and a commit.

The first version includes:

- Teacher registration, login, JWT auth, and teacher-scoped business APIs.
- Classes, students, student Excel import, courses, weekly schedules.
- Exams with participating classes, subjects, score snapshots, score entry, score import.
- Import batches and row-level import errors.
- Statistics for exams, rankings, segments, student history, class overview.
- Dashboard summary, today schedule, recent exams, score overview, class average trend.
- Frontend pages and workflows from the frontend workflow design.

The first version excludes:

- School admin, student login, parent login, SSO, refresh tokens.
- Advanced schedule conflict detection, cancellations, makeups, term schedule versions.
- Frontend recalculation of backend statistics rules.

## Implementation Assumptions

- Visible UI copy should be Chinese for teacher-facing labels and messages, while route names, component names, API fields, and code identifiers stay English.
- Backend unit and service tests use SQLite in-memory where engine-specific behavior is not under test; Alembic migration smoke tests run against MySQL through `docker-compose.yml`.
- Decimal scores use `Decimal` in Python and `DECIMAL(6,2)` in the database; frontend sends score values as strings or numbers and backend normalizes to `Decimal`.
- Soft deletion means setting `status` to `inactive` unless the service explicitly sets `archived`.
- Default application timezone is `Asia/Shanghai` and is configurable through `APP_TIMEZONE`.

## Target File Structure

Create this structure during implementation:

```text
backend/
  alembic.ini
  pyproject.toml
  app/
    __init__.py
    main.py
    api.py
    core/
      config.py
      database.py
      deps.py
      errors.py
      pagination.py
      security.py
      time.py
    models/
      __init__.py
      base.py
      teacher.py
      class_.py
      student.py
      course.py
      schedule.py
      exam.py
      score.py
      import_.py
    modules/
      auth/
        router.py
        schemas.py
        service.py
      classes/
        router.py
        schemas.py
        service.py
      students/
        router.py
        schemas.py
        service.py
        import_service.py
      courses/
        router.py
        schemas.py
        service.py
      schedules/
        router.py
        schemas.py
        service.py
      exams/
        router.py
        schemas.py
        service.py
        roster_service.py
      scores/
        router.py
        schemas.py
        service.py
        import_service.py
        template_service.py
      imports/
        router.py
        schemas.py
        service.py
      statistics/
        router.py
        schemas.py
        service.py
      dashboard/
        router.py
        schemas.py
        service.py
    tests/
      conftest.py
      test_auth.py
      test_classes_students_courses_schedules.py
      test_exams_rosters.py
      test_scores.py
      test_student_import.py
      test_score_import.py
      test_statistics.py
      test_dashboard.py
frontend/
  package.json
  index.html
  vite.config.ts
  tsconfig.json
  playwright.config.ts
  src/
    main.ts
    App.vue
    router/
      index.ts
    stores/
      auth.ts
    api/
      http.ts
      auth.ts
      classes.ts
      students.ts
      courses.ts
      schedules.ts
      exams.ts
      scores.ts
      imports.ts
      statistics.ts
      dashboard.ts
    layouts/
      AppLayout.vue
    views/
      LoginView.vue
      RegisterView.vue
      DashboardView.vue
      ClassesStudentsView.vue
      CoursesScheduleView.vue
      ExamCenterView.vue
      ExamDetailView.vue
      ScoreEntryView.vue
      ExamStatisticsView.vue
      ImportRecordsView.vue
      ImportDetailView.vue
      AccountSettingsView.vue
    components/
      common/
        PageHeader.vue
        StatusTag.vue
        EmptyState.vue
      dashboard/
        MetricCard.vue
        TodaySchedule.vue
        RecentExams.vue
        ScoreOverviewCard.vue
        ClassAverageTrend.vue
      exams/
        ExamWizard.vue
        ExamBasicStep.vue
        ExamClassesStep.vue
        ExamSubjectsStep.vue
        ExamConfirmStep.vue
      scores/
        ScoreEntryTable.vue
        ScoreImportDialog.vue
      imports/
        ImportResultPanel.vue
        ImportErrorTable.vue
    styles/
      tokens.css
      app.css
  tests/
    auth.spec.ts
    dashboard.spec.ts
    exam-workflow.spec.ts
    score-entry.spec.ts
    import-records.spec.ts
  e2e/
    grade-manager.spec.ts
docker-compose.yml
.env.example
```

## Backend Data Contract

Use these ORM names consistently:

- `Teacher`: `id`, `username`, `password_hash`, `display_name`, `email`, `phone`, `status`, `created_at`, `updated_at`
- `Class`: `id`, `teacher_id`, `name`, `grade`, `academic_year`, `status`, `remark`, `created_at`, `updated_at`
- `Student`: `id`, `teacher_id`, `class_id`, `student_no`, `name`, `gender`, `status`, `remark`, `created_at`, `updated_at`
- `Course`: `id`, `teacher_id`, `course_name`, `status`, `remark`, `created_at`, `updated_at`
- `Schedule`: `id`, `teacher_id`, `class_id`, `course_id`, `weekday`, `period_no`, `start_time`, `end_time`, `location`, `status`, `remark`, `created_at`, `updated_at`
- `Exam`: `id`, `teacher_id`, `name`, `exam_type`, `term`, `status`, `remark`, `created_at`, `updated_at`
- `ExamClass`: `id`, `exam_id`, `class_id`, `status`, `created_at`
- `ExamSubject`: `id`, `exam_id`, `course_id`, `full_score`, `pass_score`, `excellent_score`, `exam_date`, `status`, `remark`, `created_at`, `updated_at`
- `ExamStudent`: `id`, `exam_id`, `student_id`, `class_id`, `status`, `created_at`
- `Score`: `id`, `exam_student_id`, `exam_subject_id`, `score`, `score_status`, `remark`, `created_at`, `updated_at`
- `ImportBatch`: `id`, `teacher_id`, `import_type`, `target_class_id`, `target_exam_id`, `target_exam_subject_id`, `file_name`, `status`, `success_count`, `failed_count`, `error_summary`, `created_at`, `updated_at`
- `ImportError`: `id`, `batch_id`, `row_number`, `field`, `raw_value`, `reason`, `raw_data`, `created_at`

Use these enum values:

```python
ACTIVE_STATUSES = ("active", "inactive", "archived")
EXAM_CLASS_STATUSES = ("active", "inactive")
EXAM_STUDENT_STATUSES = ("active", "withdrawn", "inactive")
SCORE_STATUSES = ("normal", "absent", "deferred", "cheating", "exempt")
IMPORT_STATUSES = ("pending", "processing", "success", "partial_success", "failed")
IMPORT_TYPES = ("students", "scores")
```

## API Contract

All paths are under `/api/v1`.

- Auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- Classes: `GET /classes`, `POST /classes`, `PATCH /classes/{id}`, `DELETE /classes/{id}`
- Students: `GET /students`, `POST /students`, `PATCH /students/{id}`, `DELETE /students/{id}`, `POST /students/import`
- Courses: `GET /courses`, `POST /courses`, `PATCH /courses/{id}`, `DELETE /courses/{id}`
- Schedules: `GET /schedules`, `POST /schedules`, `PATCH /schedules/{id}`, `DELETE /schedules/{id}`
- Exams: `GET /exams`, `POST /exams`, `GET /exams/{id}`, `PATCH /exams/{id}`, `DELETE /exams/{id}`, `PUT /exams/{id}/classes`, `PUT /exams/{id}/subjects`
- Scores: `GET /exams/{id}/score-sheet`, `PUT /exams/{id}/scores`, `GET /exams/{id}/score-template`, `POST /exams/{id}/scores/import`
- Imports: `GET /imports`, `GET /imports/{id}`, `GET /imports/{id}/errors`
- Statistics: `GET /statistics/exams/{id}/summary`, `GET /statistics/exams/{id}/rankings`, `GET /statistics/exams/{id}/segments`, `GET /statistics/students/{id}/history`, `GET /statistics/classes/{id}/overview`
- Dashboard: `GET /dashboard/summary`, `GET /dashboard/today-schedule`, `GET /dashboard/recent-exams`, `GET /dashboard/score-overview`, `GET /dashboard/class-average-trend`

Error responses must use:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "成绩保存失败",
  "details": [
    {
      "field": "score",
      "row": 12,
      "value": "108",
      "reason": "分数不能超过满分 100"
    }
  ]
}
```

## Task 1: Repository And Backend Skeleton

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `backend/pyproject.toml`
- Create: `backend/app/main.py`
- Create: `backend/app/api.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`
- Create: `backend/app/core/errors.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [ ] **Step 1: Write the failing backend health test**

```python
# backend/tests/test_health.py
def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Create backend package metadata**

```toml
# backend/pyproject.toml
[project]
name = "grade-manager-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "alembic>=1.13.3",
  "email-validator>=2.2.0",
  "fastapi>=0.115.0",
  "openpyxl>=3.1.5",
  "passlib[bcrypt]>=1.7.4",
  "pydantic-settings>=2.5.2",
  "pymysql>=1.1.1",
  "python-jose[cryptography]>=3.3.0",
  "python-multipart>=0.0.12",
  "sqlalchemy>=2.0.35",
  "uvicorn[standard]>=0.30.6"
]

[project.optional-dependencies]
dev = [
  "httpx>=0.27.2",
  "pytest>=8.3.3",
  "pytest-cov>=5.0.0",
  "ruff>=0.6.9"
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py312"
```

- [ ] **Step 3: Add environment and MySQL development service**

```yaml
# docker-compose.yml
services:
  mysql:
    image: mysql:8.4
    environment:
      MYSQL_DATABASE: grade_manager
      MYSQL_USER: grade_manager
      MYSQL_PASSWORD: grade_manager
      MYSQL_ROOT_PASSWORD: grade_manager_root
    ports:
      - "3306:3306"
    volumes:
      - grade_manager_mysql:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 3s
      retries: 20

volumes:
  grade_manager_mysql:
```

```dotenv
# .env.example
DATABASE_URL=mysql+pymysql://grade_manager:grade_manager@127.0.0.1:3306/grade_manager
SECRET_KEY=change-me-in-local-env
ACCESS_TOKEN_EXPIRE_DAYS=30
APP_TIMEZONE=Asia/Shanghai
BACKEND_CORS_ORIGINS=http://localhost:5173
```

- [ ] **Step 4: Implement FastAPI app factory and health route**

```python
# backend/app/core/config.py
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+pysqlite:///:memory:"
    secret_key: str = "dev-secret"
    access_token_expire_days: int = 30
    app_timezone: str = "Asia/Shanghai"
    backend_cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```python
# backend/app/core/database.py
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

```python
# backend/app/core/errors.py
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str | None = None
    row: int | None = None
    value: str | None = None
    reason: str


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[ErrorDetail] | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or []


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.code,
            "message": exc.message,
            "details": [detail.model_dump(exclude_none=True) for detail in exc.details],
        },
    )
```

```python
# backend/app/api.py
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router
from app.core.config import get_settings
from app.core.errors import AppError, app_error_handler


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Grade Manager API")
    origins = [origin.strip() for origin in settings.backend_cors_origins.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.include_router(api_router)
    return app


app = create_app()
```

```python
# backend/tests/conftest.py
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client():
    return TestClient(create_app())
```

- [ ] **Step 5: Run health test**

Run:

```bash
cd backend
uv sync --extra dev
uv run pytest tests/test_health.py -v
```

Expected:

```text
tests/test_health.py::test_health PASSED
```

- [ ] **Step 6: Commit**

```bash
git add .env.example docker-compose.yml backend
git commit -m "chore: scaffold backend application"
```

## Task 2: Shared ORM Models, Migrations, Pagination, And Error Utilities

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial_schema.py`
- Create: `backend/app/models/*.py`
- Create: `backend/app/core/pagination.py`
- Modify: `backend/app/core/database.py`
- Test: `backend/tests/test_schema_contract.py`

- [ ] **Step 1: Write schema contract tests**

```python
# backend/tests/test_schema_contract.py
from decimal import Decimal

from sqlalchemy import inspect

from app.core.database import Base, engine
from app.models import (
    Class,
    Course,
    Exam,
    ExamClass,
    ExamStudent,
    ExamSubject,
    ImportBatch,
    ImportError,
    Schedule,
    Score,
    Student,
    Teacher,
)


def test_all_expected_tables_are_registered():
    assert {
        "teachers",
        "classes",
        "students",
        "courses",
        "schedules",
        "exams",
        "exam_classes",
        "exam_subjects",
        "exam_students",
        "scores",
        "import_batches",
        "import_errors",
    } <= set(Base.metadata.tables)


def test_score_column_uses_decimal_scale():
    score_column = Score.__table__.c.score
    assert score_column.type.scale == 2
    assert score_column.type.precision == 6
    assert Decimal("99.50") == Decimal("99.50")


def test_unique_constraints_exist():
    constraints = {
        constraint.name
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if constraint.name
    }
    assert "uq_students_teacher_student_no" in constraints
    assert "uq_courses_teacher_course_name" in constraints
    assert "uq_schedules_active_slot" in constraints
    assert "uq_exam_classes_exam_class" in constraints
    assert "uq_exam_subjects_exam_course" in constraints
    assert "uq_exam_students_exam_student" in constraints
    assert "uq_scores_exam_student_subject" in constraints


def test_models_can_create_sqlite_schema():
    Base.metadata.create_all(bind=engine)
    table_names = inspect(engine).get_table_names()
    assert "teachers" in table_names
    assert "scores" in table_names
```

- [ ] **Step 2: Implement `TimestampMixin` and `Base` imports**

```python
# backend/app/models/base.py
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
```

- [ ] **Step 3: Implement ORM models with exact table and constraint names**

Use `backend/app/models/teacher.py`, `class_.py`, `student.py`, `course.py`, `schedule.py`, `exam.py`, `score.py`, and `import_.py`. The `Score.score` and exam threshold columns must use `Numeric(6, 2)`. Use `String(20)` for status columns, `Text` for remarks and raw JSON text, `Time` for schedule times, and `Date` for exam subject dates.

The `Schedule` unique active slot is implemented as a normal unique constraint in the first migration:

```python
UniqueConstraint(
    "teacher_id",
    "class_id",
    "weekday",
    "period_no",
    name="uq_schedules_active_slot",
)
```

The service layer must enforce active-only semantics when restoring or creating schedule slots because MySQL does not support a portable filtered unique constraint.

- [ ] **Step 4: Implement `backend/app/models/__init__.py` exports**

```python
from app.models.class_ import Class
from app.models.course import Course
from app.models.exam import Exam, ExamClass, ExamStudent, ExamSubject
from app.models.import_ import ImportBatch, ImportError
from app.models.schedule import Schedule
from app.models.score import Score
from app.models.student import Student
from app.models.teacher import Teacher

__all__ = [
    "Class",
    "Course",
    "Exam",
    "ExamClass",
    "ExamStudent",
    "ExamSubject",
    "ImportBatch",
    "ImportError",
    "Schedule",
    "Score",
    "Student",
    "Teacher",
]
```

- [ ] **Step 5: Add pagination helper**

```python
# backend/app/core/pagination.py
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class PageParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


def paginate(db: Session, query: Select, page: int, page_size: int) -> tuple[list, int]:
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset((page - 1) * page_size).limit(page_size)).all()
    return list(items), total
```

- [ ] **Step 6: Run schema tests**

Run:

```bash
cd backend
uv run pytest tests/test_schema_contract.py -v
```

Expected:

```text
tests/test_schema_contract.py::test_all_expected_tables_are_registered PASSED
tests/test_schema_contract.py::test_score_column_uses_decimal_scale PASSED
tests/test_schema_contract.py::test_unique_constraints_exist PASSED
tests/test_schema_contract.py::test_models_can_create_sqlite_schema PASSED
```

- [ ] **Step 7: Commit**

```bash
git add backend
git commit -m "feat: add backend data model schema"
```

## Task 3: Authentication And Teacher Scoping Foundation

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/core/deps.py`
- Create: `backend/app/modules/auth/router.py`
- Create: `backend/app/modules/auth/schemas.py`
- Create: `backend/app/modules/auth/service.py`
- Modify: `backend/app/api.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write auth tests**

```python
# backend/tests/test_auth.py
from datetime import timedelta

from app.core.security import create_access_token, decode_access_token


def test_register_login_and_me(client):
    register = client.post(
        "/api/v1/auth/register",
        json={
            "username": "teacher1",
            "password": "strong-password",
            "display_name": "王老师",
            "email": "teacher1@example.com",
            "phone": "13800000000",
        },
    )
    assert register.status_code == 201
    assert register.json()["username"] == "teacher1"
    assert "password_hash" not in register.json()

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "teacher1", "password": "strong-password"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["display_name"] == "王老师"


def test_duplicate_username_returns_409(client):
    payload = {"username": "teacher1", "password": "strong-password", "display_name": "王老师"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["code"] == "DUPLICATE_RESOURCE"


def test_expired_token_is_rejected(client):
    token = create_access_token(subject="1", expires_delta=timedelta(seconds=-1))
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"


def test_token_contains_teacher_id():
    token = create_access_token(subject="42", expires_delta=timedelta(days=30))
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert "exp" in payload
```

- [ ] **Step 2: Implement password hashing and JWT helpers**

```python
# backend/app/core/security.py
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.errors import AppError

ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(days=settings.access_token_expire_days)
    )
    return jwt.encode({"sub": subject, "exp": expire}, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise AppError(401, "UNAUTHORIZED", "登录已过期，请重新登录") from exc
```

- [ ] **Step 3: Implement auth schemas**

```python
# backend/app/modules/auth/schemas.py
from pydantic import BaseModel, EmailStr, Field


class TeacherRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class TeacherLogin(BaseModel):
    username: str
    password: str


class TeacherRead(BaseModel):
    id: int
    username: str
    display_name: str
    email: str | None
    phone: str | None
    status: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    teacher: TeacherRead
```

- [ ] **Step 4: Implement current-teacher dependency**

```python
# backend/app/core/deps.py
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models import Teacher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_teacher(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Teacher:
    payload = decode_access_token(token)
    teacher_id = payload.get("sub")
    if not teacher_id:
        raise AppError(401, "UNAUTHORIZED", "登录已过期，请重新登录")
    teacher = db.get(Teacher, int(teacher_id))
    if teacher is None or teacher.status != "active":
        raise AppError(401, "UNAUTHORIZED", "登录已过期，请重新登录")
    return teacher
```

- [ ] **Step 5: Implement auth service and router**

The service must:

- Reject duplicate `username` with `409 DUPLICATE_RESOURCE`.
- Store `password_hash` only.
- Reject inactive teachers during login.
- Return `TeacherRead` and token from login.

The router registers:

```python
router = APIRouter(prefix="/auth", tags=["auth"])
router.post("/register", status_code=201)
router.post("/login")
router.get("/me")
```

Mount it in `backend/app/api.py`:

```python
from app.modules.auth.router import router as auth_router

api_router.include_router(auth_router)
```

- [ ] **Step 6: Run auth tests**

Run:

```bash
cd backend
uv run pytest tests/test_auth.py -v
```

Expected:

```text
4 passed
```

- [ ] **Step 7: Commit**

```bash
git add backend
git commit -m "feat: add teacher authentication"
```

## Task 4: Classes, Students, Courses, And Schedules CRUD

**Files:**
- Create: `backend/app/modules/classes/*`
- Create: `backend/app/modules/students/schemas.py`
- Create: `backend/app/modules/students/service.py`
- Create: `backend/app/modules/students/router.py`
- Create: `backend/app/modules/courses/*`
- Create: `backend/app/modules/schedules/*`
- Modify: `backend/app/api.py`
- Test: `backend/tests/test_classes_students_courses_schedules.py`

- [ ] **Step 1: Write CRUD and ownership tests**

```python
# backend/tests/test_classes_students_courses_schedules.py
def auth_headers(client, username):
    client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": "strong-password", "display_name": username},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": "strong-password"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_teacher_scoped_classes_students_courses_and_schedules(client):
    t1 = auth_headers(client, "teacher1")
    t2 = auth_headers(client, "teacher2")

    class_response = client.post(
        "/api/v1/classes",
        headers=t1,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027", "remark": ""},
    )
    assert class_response.status_code == 201
    class_id = class_response.json()["id"]

    assert client.get("/api/v1/classes", headers=t2).json()["total"] == 0

    student = client.post(
        "/api/v1/students",
        headers=t1,
        json={"class_id": class_id, "student_no": "S001", "name": "张三", "gender": "男"},
    )
    assert student.status_code == 201

    duplicate = client.post(
        "/api/v1/students",
        headers=t1,
        json={"class_id": class_id, "student_no": "S001", "name": "李四"},
    )
    assert duplicate.status_code == 409

    course = client.post(
        "/api/v1/courses",
        headers=t1,
        json={"course_name": "数学", "remark": ""},
    )
    assert course.status_code == 201
    course_id = course.json()["id"]

    schedule = client.post(
        "/api/v1/schedules",
        headers=t1,
        json={
            "class_id": class_id,
            "course_id": course_id,
            "weekday": 1,
            "period_no": 1,
            "start_time": "08:00",
            "end_time": "08:45",
            "location": "教学楼 A101",
        },
    )
    assert schedule.status_code == 201


def test_schedule_rejects_invalid_time_order(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "语文"},
    ).json()["id"]

    response = client.post(
        "/api/v1/schedules",
        headers=headers,
        json={
            "class_id": class_id,
            "course_id": course_id,
            "weekday": 1,
            "period_no": 1,
            "start_time": "09:00",
            "end_time": "08:45",
        },
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
```

- [ ] **Step 2: Implement list schemas with pagination**

Every list endpoint returns:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

For `GET /students`, support `page`, `page_size`, `keyword`, `status`, and `class_id`. For `GET /classes`, `GET /courses`, and `GET /schedules`, support `page`, `page_size`, `keyword`, and `status`; schedules also support `class_id`.

- [ ] **Step 3: Implement service ownership rules**

Services must check these exact rules before writing:

- Class writes always set `teacher_id=current_teacher.id`.
- Student `class_id` must belong to current teacher; student `teacher_id` must equal current teacher id.
- Course writes always set `teacher_id=current_teacher.id`.
- Schedule `class_id` and `course_id` must both belong to current teacher.
- `weekday` must be 1 through 7.
- `period_no` must be greater than 0.
- If both `start_time` and `end_time` are present, `start_time < end_time`.
- Duplicate student number returns `409 DUPLICATE_RESOURCE`.
- Duplicate course name returns `409 DUPLICATE_RESOURCE`.
- Duplicate schedule slot returns `409 DUPLICATE_RESOURCE`.
- `DELETE` sets `status="inactive"` and never physically deletes rows.

- [ ] **Step 4: Implement routers and mount them**

Mount these routers in `backend/app/api.py`:

```python
from app.modules.classes.router import router as classes_router
from app.modules.courses.router import router as courses_router
from app.modules.schedules.router import router as schedules_router
from app.modules.students.router import router as students_router

api_router.include_router(classes_router)
api_router.include_router(students_router)
api_router.include_router(courses_router)
api_router.include_router(schedules_router)
```

- [ ] **Step 5: Run CRUD tests**

Run:

```bash
cd backend
uv run pytest tests/test_classes_students_courses_schedules.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: add base management APIs"
```

## Task 5: Exam Creation, Class Associations, Subject Rules, And Roster Snapshots

**Files:**
- Create: `backend/app/modules/exams/router.py`
- Create: `backend/app/modules/exams/schemas.py`
- Create: `backend/app/modules/exams/service.py`
- Create: `backend/app/modules/exams/roster_service.py`
- Modify: `backend/app/api.py`
- Test: `backend/tests/test_exams_rosters.py`

- [ ] **Step 1: Write exam and roster tests**

```python
# backend/tests/test_exams_rosters.py
from decimal import Decimal

from tests.test_classes_students_courses_schedules import auth_headers


def seed_base(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    course_id = client.post(
        "/api/v1/courses",
        headers=headers,
        json={"course_name": "数学"},
    ).json()["id"]
    student_id = client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S001", "name": "张三"},
    ).json()["id"]
    return headers, class_id, course_id, student_id


def test_create_exam_with_classes_subjects_and_snapshot(client):
    headers, class_id, course_id, student_id = seed_base(client)
    response = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "remark": "",
            "class_ids": [class_id],
            "subjects": [
                {
                    "course_id": course_id,
                    "full_score": "100.00",
                    "pass_score": "60.00",
                    "excellent_score": "90.00",
                    "exam_date": "2026-10-20",
                    "remark": "",
                }
            ],
        },
    )
    assert response.status_code == 201
    exam = response.json()
    assert exam["name"] == "期中考试"
    assert exam["classes"][0]["id"] == class_id
    assert exam["subjects"][0]["course_id"] == course_id

    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers)
    assert sheet.status_code == 200
    assert sheet.json()["students"][0]["student_id"] == student_id


def test_exam_rejects_invalid_threshold_order(client):
    headers, class_id, course_id, _ = seed_base(client)
    response = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "单元测验",
            "exam_type": "quiz",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [
                {
                    "course_id": course_id,
                    "full_score": "100.00",
                    "pass_score": "95.00",
                    "excellent_score": "90.00",
                }
            ],
        },
    )
    assert response.status_code == 422
    assert response.json()["details"][0]["field"] == "subjects.pass_score"


def test_roster_refresh_appends_after_scoring_without_rewriting_existing_rows(client):
    headers, class_id, course_id, student_id = seed_base(client)
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    first_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    exam_student_id = first_sheet["students"][0]["exam_student_id"]
    exam_subject_id = first_sheet["subjects"][0]["exam_subject_id"]

    save = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": exam_student_id,
                    "exam_subject_id": exam_subject_id,
                    "score": "88",
                    "score_status": "normal",
                    "remark": "",
                }
            ]
        },
    )
    assert save.status_code == 200

    client.post(
        "/api/v1/students",
        headers=headers,
        json={"class_id": class_id, "student_no": "S002", "name": "李四"},
    )
    second_sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    assert len(second_sheet["students"]) == 2
    original = [row for row in second_sheet["students"] if row["student_id"] == student_id][0]
    assert original["exam_student_id"] == exam_student_id
```

- [ ] **Step 2: Implement exam schemas**

Required request schemas:

- `ExamCreate`: `name`, `exam_type`, `term`, `remark`, `class_ids`, `subjects`
- `ExamSubjectCreate`: `course_id`, `full_score`, `pass_score`, `excellent_score`, `exam_date`, `remark`
- `ExamUpdate`: optional `name`, `exam_type`, `term`, `status`, `remark`
- `ExamClassesUpdate`: `class_ids`
- `ExamSubjectsUpdate`: `subjects` with optional `id`, `course_id`, thresholds, status, dates, remarks

Validation rules:

```python
if not class_ids:
    raise AppError(422, "VALIDATION_ERROR", "考试至少需要一个班级")
if not subjects:
    raise AppError(422, "VALIDATION_ERROR", "考试至少需要一个科目")
if pass_score < 0 or excellent_score < 0 or full_score < 0:
    raise AppError(422, "VALIDATION_ERROR", "分数阈值不能为负数")
if pass_score > excellent_score or excellent_score > full_score:
    raise AppError(
        422,
        "VALIDATION_ERROR",
        "分数阈值必须满足 0 <= 及格分 <= 优秀分 <= 满分",
        [ErrorDetail(field="subjects.pass_score", reason="分数阈值顺序错误")],
    )
```

- [ ] **Step 3: Implement roster service**

`ensure_exam_roster(db, exam)` must:

- Read active `ExamClass` rows for the exam.
- Read active `Student` rows from those classes.
- If the exam has no scores, rebuild `ExamStudent` rows from current active students.
- If the exam has scores, retain all existing `ExamStudent` rows, retain all scores, append new active students from active exam classes, and never change existing `ExamStudent.class_id`.

`has_exam_scores(db, exam_id)` returns true when any score exists for the exam by joining `Score -> ExamSubject`.

- [ ] **Step 4: Implement class and subject update rules**

`PUT /exams/{id}/classes` must:

- Reject class ids not owned by current teacher.
- Before scoring starts, replace active class associations and rebuild the roster.
- After scoring starts, append new classes and students through roster merge.
- After scoring starts, reject removing a class when any score exists for snapshotted students in that class.
- After scoring starts, mark removable classes inactive and mark related exam students inactive instead of deleting rows.

`PUT /exams/{id}/subjects` must:

- Reject courses not owned by current teacher.
- Reject duplicate course ids.
- Remove only subjects with no scores.
- Preserve subjects with scores; allow threshold/date/status/remark updates.
- Reject new `full_score` below the highest existing normal score for the subject.

- [ ] **Step 5: Mount exams router and run tests**

Run:

```bash
cd backend
uv run pytest tests/test_exams_rosters.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: add exam setup and roster snapshots"
```

## Task 6: Score Sheet, Bulk Score Save, And Item-Level Failures

**Files:**
- Create: `backend/app/modules/scores/router.py`
- Create: `backend/app/modules/scores/schemas.py`
- Create: `backend/app/modules/scores/service.py`
- Create: `backend/app/modules/scores/template_service.py`
- Modify: `backend/app/api.py`
- Test: `backend/tests/test_scores.py`

- [ ] **Step 1: Write score tests**

```python
# backend/tests/test_scores.py
from tests.test_exams_rosters import seed_base


def create_exam_sheet(client):
    headers, class_id, course_id, _ = seed_base(client)
    exam = client.post(
        "/api/v1/exams",
        headers=headers,
        json={
            "name": "期中考试",
            "exam_type": "school",
            "term": "2026-2027-1",
            "class_ids": [class_id],
            "subjects": [{"course_id": course_id, "full_score": "100", "pass_score": "60", "excellent_score": "90"}],
        },
    ).json()
    sheet = client.get(f"/api/v1/exams/{exam['id']}/score-sheet", headers=headers).json()
    return headers, exam, sheet


def test_bulk_score_save_returns_item_failures(client):
    headers, exam, sheet = create_exam_sheet(client)
    exam_student_id = sheet["students"][0]["exam_student_id"]
    exam_subject_id = sheet["subjects"][0]["exam_subject_id"]

    response = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": exam_student_id,
                    "exam_subject_id": exam_subject_id,
                    "score": "88",
                    "score_status": "normal",
                    "remark": "",
                },
                {
                    "exam_student_id": exam_student_id,
                    "exam_subject_id": exam_subject_id,
                    "score": "108",
                    "score_status": "normal",
                    "remark": "",
                },
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 1
    assert body["failure_count"] == 1
    assert body["failed_items"][0]["reason"] == "分数不能超过满分 100.00"


def test_abnormal_score_status_requires_null_score(client):
    headers, exam, sheet = create_exam_sheet(client)
    response = client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": sheet["students"][0]["exam_student_id"],
                    "exam_subject_id": sheet["subjects"][0]["exam_subject_id"],
                    "score": "60",
                    "score_status": "absent",
                }
            ]
        },
    )
    assert response.json()["success_count"] == 0
    assert response.json()["failed_items"][0]["reason"] == "异常状态不能填写数字成绩"
```

- [ ] **Step 2: Implement score sheet response**

`GET /exams/{id}/score-sheet` returns:

```json
{
  "exam": {"id": 1, "name": "期中考试", "exam_type": "school", "term": "2026-2027-1"},
  "classes": [{"id": 1, "name": "一班"}],
  "subjects": [
    {
      "exam_subject_id": 1,
      "course_id": 1,
      "course_name": "数学",
      "full_score": "100.00",
      "pass_score": "60.00",
      "excellent_score": "90.00",
      "status": "active"
    }
  ],
  "students": [
    {
      "exam_student_id": 1,
      "student_id": 1,
      "class_id": 1,
      "student_no": "S001",
      "name": "张三",
      "status": "active"
    }
  ],
  "scores": [
    {
      "exam_student_id": 1,
      "exam_subject_id": 1,
      "score": "88.00",
      "score_status": "normal",
      "remark": ""
    }
  ]
}
```

- [ ] **Step 3: Implement bulk save validation**

For each item:

- Verify `exam_student_id` belongs to the requested exam.
- Verify `exam_subject_id` belongs to the requested exam.
- Reject request payload keys `student_id` and `class_id` with item failure reason `成绩保存不能直接指定学生或班级`.
- If `score_status="normal"`, require `score` and require `0 <= score <= full_score`.
- If `score_status` is `absent`, `deferred`, `cheating`, or `exempt`, require `score is None`.
- Upsert by `exam_student_id + exam_subject_id`.
- Return HTTP 200 with `success_count`, `failure_count`, and `failed_items` even when some items fail.
- Use one transaction and commit valid rows; invalid rows do not block valid rows.

- [ ] **Step 4: Implement template endpoint**

`GET /exams/{id}/score-template` must return an `.xlsx` file with:

- Header row: `student_no`, `student_name`, `class_name`, one column per active exam subject.
- Optional `class_id` query filter for multi-class exams.
- Template rows from `exam_students`, not current `students.class_id`.

- [ ] **Step 5: Run score tests**

Run:

```bash
cd backend
uv run pytest tests/test_scores.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit**

```bash
git add backend
git commit -m "feat: add score sheet and bulk save"
```

## Task 7: Student Import, Score Import, And Import Records

**Files:**
- Create: `backend/app/modules/students/import_service.py`
- Create: `backend/app/modules/scores/import_service.py`
- Create: `backend/app/modules/imports/router.py`
- Create: `backend/app/modules/imports/schemas.py`
- Create: `backend/app/modules/imports/service.py`
- Modify: `backend/app/modules/students/router.py`
- Modify: `backend/app/modules/scores/router.py`
- Modify: `backend/app/api.py`
- Test: `backend/tests/test_student_import.py`
- Test: `backend/tests/test_score_import.py`

- [ ] **Step 1: Write student import tests**

```python
# backend/tests/test_student_import.py
from io import BytesIO

from openpyxl import Workbook

from tests.test_classes_students_courses_schedules import auth_headers


def workbook_bytes(rows):
    wb = Workbook()
    ws = wb.active
    ws.append(["student_no", "name", "gender", "remark"])
    for row in rows:
        ws.append(row)
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream


def test_student_import_writes_valid_rows_and_records_errors(client):
    headers = auth_headers(client, "teacher1")
    class_id = client.post(
        "/api/v1/classes",
        headers=headers,
        json={"name": "一班", "grade": "七年级", "academic_year": "2026-2027"},
    ).json()["id"]
    file_obj = workbook_bytes([["S001", "张三", "男", ""], ["S001", "重复", "女", ""]])

    response = client.post(
        f"/api/v1/students/import?target_class_id={class_id}",
        headers=headers,
        files={"file": ("students.xlsx", file_obj, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 1
    assert body["failed_count"] == 1
    assert body["status"] == "partial_success"

    errors = client.get(f"/api/v1/imports/{body['batch_id']}/errors", headers=headers)
    assert errors.json()["items"][0]["row_number"] == 3
    assert errors.json()["items"][0]["field"] == "student_no"
```

- [ ] **Step 2: Write score import tests**

```python
# backend/tests/test_score_import.py
from io import BytesIO

from openpyxl import Workbook

from tests.test_scores import create_exam_sheet


def score_workbook(student_no, subject_name, value):
    wb = Workbook()
    ws = wb.active
    ws.append(["student_no", "student_name", "class_name", subject_name])
    ws.append([student_no, "张三", "一班", value])
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream


def test_score_import_uses_exam_snapshot_and_records_invalid_rows(client):
    headers, exam, sheet = create_exam_sheet(client)
    file_obj = score_workbook("S001", sheet["subjects"][0]["course_name"], "108")

    response = client.post(
        f"/api/v1/exams/{exam['id']}/scores/import",
        headers=headers,
        files={"file": ("scores.xlsx", file_obj, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success_count"] == 0
    assert body["failed_count"] == 1
    assert body["status"] == "failed"
```

- [ ] **Step 3: Implement import batch lifecycle**

For both import types:

1. Create `ImportBatch` with `status="processing"` before parsing rows.
2. Parse workbook with `openpyxl.load_workbook(file.file, data_only=True)`.
3. Treat row 1 as header.
4. Write every valid row.
5. Store every invalid row in `ImportError`.
6. Set status:
   - `success` when `success_count > 0` and `failed_count == 0`
   - `partial_success` when both counts are greater than 0
   - `failed` when `success_count == 0` and `failed_count > 0`
7. Return `batch_id`, `status`, `success_count`, `failed_count`, and `error_summary`.

- [ ] **Step 4: Implement student import row rules**

Required columns: `student_no`, `name`. Optional columns: `gender`, `status`, `remark`.

Reject a row when:

- `student_no` is blank.
- `name` is blank.
- `student_no` already exists for teacher and `update_existing=false`.
- The same workbook already contained the same `student_no`; the later row fails.
- `target_class_id` is not owned by current teacher.

When `update_existing=true`, update `name`, `gender`, `class_id`, `status`, and `remark` for existing students owned by current teacher.

- [ ] **Step 5: Implement score import row rules**

Resolve rows through `exam_students`:

- `student_no` must match a student in the exam snapshot.
- Subject columns must match active exam subject course names.
- Blank subject cell means no write for that subject.
- Normal numeric value writes `score_status="normal"` and numeric score.
- Values `absent`, `deferred`, `cheating`, and `exempt` write abnormal status with null score.
- Numeric scores must be within `0..full_score`.
- Existing scores fail unless `overwrite_existing=true`.
- Duplicate `exam_student + exam_subject` in the workbook fails for later occurrences.

- [ ] **Step 6: Implement import record endpoints**

`GET /imports` supports `page`, `page_size`, `import_type`, `status`, and `keyword`.

`GET /imports/{id}` returns batch metadata and target display names.

`GET /imports/{id}/errors` returns paginated row errors ordered by row number and id.

- [ ] **Step 7: Run import tests**

Run:

```bash
cd backend
uv run pytest tests/test_student_import.py tests/test_score_import.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 8: Commit**

```bash
git add backend
git commit -m "feat: add excel imports and import records"
```

## Task 8: Statistics And Dashboard APIs

**Files:**
- Create: `backend/app/core/time.py`
- Create: `backend/app/modules/statistics/router.py`
- Create: `backend/app/modules/statistics/schemas.py`
- Create: `backend/app/modules/statistics/service.py`
- Create: `backend/app/modules/dashboard/router.py`
- Create: `backend/app/modules/dashboard/schemas.py`
- Create: `backend/app/modules/dashboard/service.py`
- Modify: `backend/app/api.py`
- Test: `backend/tests/test_statistics.py`
- Test: `backend/tests/test_dashboard.py`

- [ ] **Step 1: Write statistics tests**

```python
# backend/tests/test_statistics.py
from tests.test_scores import create_exam_sheet


def test_exam_summary_defaults_to_normal_scores_only(client):
    headers, exam, sheet = create_exam_sheet(client)
    student = sheet["students"][0]
    subject = sheet["subjects"][0]
    client.put(
        f"/api/v1/exams/{exam['id']}/scores",
        headers=headers,
        json={
            "items": [
                {
                    "exam_student_id": student["exam_student_id"],
                    "exam_subject_id": subject["exam_subject_id"],
                    "score": "88",
                    "score_status": "normal",
                }
            ]
        },
    )
    response = client.get(f"/api/v1/statistics/exams/{exam['id']}/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["overall"]["average_score"] == "88.00"
    assert body["overall"]["pass_rate"] == "100.00"
    assert body["abnormal_counts"]["absent"] == 0
    assert body["missing_score_count"] == 0


def test_segments_and_rankings_use_backend_included_statuses(client):
    headers, exam, sheet = create_exam_sheet(client)
    response = client.get(
        f"/api/v1/statistics/exams/{exam['id']}/segments?type=total&step=10&included_statuses=missing",
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["included_statuses"] == ["missing"]
```

- [ ] **Step 2: Write dashboard tests**

```python
# backend/tests/test_dashboard.py
from tests.test_scores import create_exam_sheet


def test_dashboard_summary_and_recent_exams(client):
    headers, exam, _ = create_exam_sheet(client)
    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["class_count"] == 1
    assert summary.json()["student_count"] == 1
    assert summary.json()["course_count"] == 1
    assert summary.json()["pending_score_count"] >= 1

    recent = client.get("/api/v1/dashboard/recent-exams", headers=headers)
    assert recent.status_code == 200
    assert recent.json()["items"][0]["id"] == exam["id"]
```

- [ ] **Step 3: Implement included status calculation**

`included_statuses` is parsed as a comma-separated set from `normal`, `absent`, `deferred`, `cheating`, `exempt`, and `missing`. Default is `["normal"]`.

Score value rules:

- `normal`: use numeric score.
- `absent`, `deferred`, `cheating`, `exempt`: count as `0` only when explicitly included.
- `missing`: no `Score` row; count as `0` only when explicitly included.
- Excluded statuses are removed from numerator and denominator for average, total, ranking, segments, pass rate, and excellent rate.
- Abnormal counts and missing counts are returned separately no matter which statuses are included.

- [ ] **Step 4: Implement summary response**

`GET /statistics/exams/{id}/summary` returns:

```json
{
  "exam": {"id": 1, "name": "期中考试"},
  "included_statuses": ["normal"],
  "overall": {
    "average_score": "88.00",
    "highest_score": "88.00",
    "lowest_score": "88.00",
    "pass_rate": "100.00",
    "excellent_rate": "0.00"
  },
  "class_comparison": [],
  "subject_comparison": [],
  "abnormal_counts": {"absent": 0, "deferred": 0, "cheating": 0, "exempt": 0},
  "missing_score_count": 0,
  "abnormal_lists": {"absent": [], "deferred": [], "cheating": [], "exempt": []},
  "missing_score_list": []
}
```

- [ ] **Step 5: Implement rankings, segments, student history, and class overview**

`rankings`:

- `rank_type=total` ranks by total included score across active subjects.
- `rank_type=subject` requires `exam_subject_id`.
- Optional `class_id` filters snapshot class.

`segments`:

- `type=total` or `type=subject`.
- `step` defaults to 10.
- Segment labels use `[start, end)` except the top segment which includes the max boundary.

`students/{id}/history`:

- Return exams where the student exists in `exam_students`.
- Resolve historical class from `exam_students.class_id`.

`classes/{id}/overview`:

- Return recent exam averages for the class snapshot.

- [ ] **Step 6: Implement dashboard services**

Dashboard endpoints:

- `/dashboard/summary`: class count, student count, course count, recent exam count, pending score count.
- `/dashboard/today-schedule`: active schedules for current weekday in configured timezone.
- `/dashboard/recent-exams`: recent exams by created time and subject exam date.
- `/dashboard/score-overview`: latest relevant exam average, highest, lowest, abnormal count, abnormal distribution, low-score warning, failing count, absent count, cheating count.
- `/dashboard/class-average-trend`: recent exam average scores grouped by class snapshot.

- [ ] **Step 7: Run statistics and dashboard tests**

Run:

```bash
cd backend
uv run pytest tests/test_statistics.py tests/test_dashboard.py -v
```

Expected:

```text
4 passed
```

- [ ] **Step 8: Commit**

```bash
git add backend
git commit -m "feat: add statistics and dashboard APIs"
```

## Task 9: Frontend Scaffold, Auth, HTTP Client, And Layout

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/index.html`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/stores/auth.ts`
- Create: `frontend/src/api/http.ts`
- Create: `frontend/src/api/auth.ts`
- Create: `frontend/src/layouts/AppLayout.vue`
- Create: `frontend/src/views/LoginView.vue`
- Create: `frontend/src/views/RegisterView.vue`
- Create: `frontend/src/views/DashboardView.vue`
- Create: `frontend/src/styles/tokens.css`
- Create: `frontend/src/styles/app.css`
- Test: `frontend/tests/auth.spec.ts`

- [ ] **Step 1: Write auth route tests**

```ts
// frontend/tests/auth.spec.ts
import { describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../src/stores/auth'

describe('auth store', () => {
  it('stores token and teacher after login success', async () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.setSession({
      access_token: 'token-1',
      token_type: 'bearer',
      teacher: { id: 1, username: 'teacher1', display_name: '王老师', email: null, phone: null, status: 'active' },
    })
    expect(auth.token).toBe('token-1')
    expect(auth.teacher?.display_name).toBe('王老师')
    expect(localStorage.getItem('grade-manager-token')).toBe('token-1')
  })

  it('clears session', () => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.setSession({
      access_token: 'token-1',
      token_type: 'bearer',
      teacher: { id: 1, username: 'teacher1', display_name: '王老师', email: null, phone: null, status: 'active' },
    })
    auth.clearSession()
    expect(auth.token).toBeNull()
    expect(auth.teacher).toBeNull()
  })
})
```

- [ ] **Step 2: Create frontend package**

```json
{
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc -b && vite build",
    "test": "vitest run",
    "test:e2e": "playwright test",
    "lint": "eslint ."
  },
  "dependencies": {
    "@element-plus/icons-vue": "^2.3.1",
    "axios": "^1.7.7",
    "element-plus": "^2.8.4",
    "pinia": "^2.2.4",
    "vue": "^3.5.10",
    "vue-router": "^4.4.5"
  },
  "devDependencies": {
    "@playwright/test": "^1.48.0",
    "@vitejs/plugin-vue": "^5.1.4",
    "@vue/test-utils": "^2.4.6",
    "typescript": "^5.6.2",
    "vite": "^5.4.8",
    "vitest": "^2.1.2",
    "vue-tsc": "^2.1.6"
  }
}
```

- [ ] **Step 3: Implement HTTP interceptor**

```ts
// frontend/src/api/http.ts
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'
import router from '../router'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
})

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.token) {
    config.headers.Authorization = `Bearer ${auth.token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error.response?.status
    const message = error.response?.data?.message || '系统错误，请稍后重试'
    if (status === 401) {
      useAuthStore().clearSession()
      await router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else if ([400, 403, 404, 409, 422].includes(status)) {
      ElMessage.error(message)
    } else {
      ElMessage.error('系统错误，请稍后重试')
    }
    return Promise.reject(error)
  },
)
```

- [ ] **Step 4: Implement protected router**

Routes:

- `/login`, `/register`
- `/` redirect to `/dashboard`
- `/dashboard`
- `/classes-students`
- `/courses-schedule`
- `/exam-center`
- `/exam-center/:id`
- `/exam-center/:id/scores`
- `/exam-center/:id/statistics`
- `/statistics`
- `/imports`
- `/imports/:id`
- `/account`

Navigation guard:

```ts
router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.token) return { path: '/login', query: { redirect: to.fullPath } }
  return true
})
```

- [ ] **Step 5: Implement desktop-first layout tokens**

`tokens.css` must define:

```css
:root {
  --gm-sidebar-width: 212px;
  --gm-bg: #f4f7f9;
  --gm-card: #ffffff;
  --gm-text: #263238;
  --gm-muted: #6b7c86;
  --gm-border: #dce6ea;
  --gm-teal: #1aa6a6;
  --gm-blue: #2f80ed;
  --gm-indigo: #5b6ee1;
  --gm-amber: #d89614;
  --gm-purple: #7c5cc4;
  --gm-green: #2f9e63;
  --gm-radius: 8px;
  --gm-gap: 10px;
}
```

`AppLayout.vue` must use a `200-220px` light teal/blue sidebar, compact `8-12px` gaps, white cards, and no dark sidebar or high-saturation metric gradients.

- [ ] **Step 6: Run frontend auth tests**

Run:

```bash
cd frontend
npm install
npm run test -- auth.spec.ts
```

Expected:

```text
2 passed
```

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "feat: scaffold frontend auth layout"
```

## Task 10: Frontend Setup Pages For Classes, Students, Courses, And Schedule

**Files:**
- Create: `frontend/src/api/classes.ts`
- Create: `frontend/src/api/students.ts`
- Create: `frontend/src/api/courses.ts`
- Create: `frontend/src/api/schedules.ts`
- Modify: `frontend/src/views/ClassesStudentsView.vue`
- Modify: `frontend/src/views/CoursesScheduleView.vue`
- Create: `frontend/src/components/imports/ImportResultPanel.vue`
- Test: `frontend/tests/base-management.spec.ts`

- [ ] **Step 1: Write component workflow tests**

```ts
// frontend/tests/base-management.spec.ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ClassesStudentsView from '../src/views/ClassesStudentsView.vue'
import CoursesScheduleView from '../src/views/CoursesScheduleView.vue'

describe('base management views', () => {
  it('renders class and student controls on one page', () => {
    const wrapper = mount(ClassesStudentsView, { global: { stubs: ['el-button', 'el-table', 'el-dialog'] } })
    expect(wrapper.text()).toContain('班级与学生')
    expect(wrapper.text()).toContain('导入学生')
    expect(wrapper.text()).toContain('新增学生')
  })

  it('renders course and weekly schedule tabs', () => {
    const wrapper = mount(CoursesScheduleView, { global: { stubs: ['el-tabs', 'el-tab-pane', 'el-table'] } })
    expect(wrapper.text()).toContain('课程管理')
    expect(wrapper.text()).toContain('周课表')
  })
})
```

- [ ] **Step 2: Implement API modules**

Each module exports list, create, update, and remove functions using `http`.

Example:

```ts
// frontend/src/api/classes.ts
import { http } from './http'

export interface ClassRecord {
  id: number
  name: string
  grade: string
  academic_year: string
  status: string
  remark?: string
}

export function listClasses(params: Record<string, unknown>) {
  return http.get('/classes', { params })
}

export function createClass(data: Partial<ClassRecord>) {
  return http.post('/classes', data)
}

export function updateClass(id: number, data: Partial<ClassRecord>) {
  return http.patch(`/classes/${id}`, data)
}

export function removeClass(id: number) {
  return http.delete(`/classes/${id}`)
}
```

- [ ] **Step 3: Implement Classes And Students view**

The page must include:

- Page title `班级与学生`.
- Class filter/list area.
- Class create/edit dialog.
- Student table with keyword search, status filter, class filter, and pagination.
- Student create/edit dialog.
- Upload control for `/students/import?target_class_id=...`.
- Immediate import result panel with success count, failure count, status, and link to `/imports/{batch_id}`.

- [ ] **Step 4: Implement Courses And Schedule view**

The page must use two tabs:

- `课程管理`: course table, create/edit dialog, status, remark.
- `周课表`: class selector, weekday, period number, optional start/end time, location, status, remark.

Validation shown in the form:

- Weekday required and in 1-7 selection labels `周一` through `周日`.
- Period number is positive.
- End time must be later than start time when both are filled.

- [ ] **Step 5: Run setup page tests**

Run:

```bash
cd frontend
npm run test -- base-management.spec.ts
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Commit**

```bash
git add frontend
git commit -m "feat: add setup management pages"
```

## Task 11: Frontend Exam Center, Exam Wizard, Score Entry, And Score Import

**Files:**
- Create: `frontend/src/api/exams.ts`
- Create: `frontend/src/api/scores.ts`
- Create: `frontend/src/components/exams/ExamWizard.vue`
- Create: `frontend/src/components/exams/ExamBasicStep.vue`
- Create: `frontend/src/components/exams/ExamClassesStep.vue`
- Create: `frontend/src/components/exams/ExamSubjectsStep.vue`
- Create: `frontend/src/components/exams/ExamConfirmStep.vue`
- Create: `frontend/src/components/scores/ScoreEntryTable.vue`
- Create: `frontend/src/components/scores/ScoreImportDialog.vue`
- Modify: `frontend/src/views/ExamCenterView.vue`
- Modify: `frontend/src/views/ExamDetailView.vue`
- Modify: `frontend/src/views/ScoreEntryView.vue`
- Test: `frontend/tests/exam-workflow.spec.ts`
- Test: `frontend/tests/score-entry.spec.ts`

- [ ] **Step 1: Write exam wizard and score entry tests**

```ts
// frontend/tests/exam-workflow.spec.ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ExamWizard from '../src/components/exams/ExamWizard.vue'

describe('exam wizard', () => {
  it('renders four required steps', () => {
    const wrapper = mount(ExamWizard, { global: { stubs: ['el-steps', 'el-step', 'el-form'] } })
    expect(wrapper.text()).toContain('基本信息')
    expect(wrapper.text()).toContain('参与班级')
    expect(wrapper.text()).toContain('考试科目')
    expect(wrapper.text()).toContain('确认创建')
  })
})
```

```ts
// frontend/tests/score-entry.spec.ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ScoreEntryTable from '../src/components/scores/ScoreEntryTable.vue'

describe('score entry table', () => {
  it('supports focused and whole-exam modes', () => {
    const wrapper = mount(ScoreEntryTable, {
      props: {
        mode: 'whole',
        students: [{ exam_student_id: 1, name: '张三', student_no: 'S001', class_id: 1 }],
        subjects: [{ exam_subject_id: 1, course_name: '数学', full_score: '100.00' }],
        scores: [],
        failedItems: [],
      },
      global: { stubs: ['el-table', 'el-input-number', 'el-select'] },
    })
    expect(wrapper.text()).toContain('张三')
    expect(wrapper.text()).toContain('数学')
  })
})
```

- [ ] **Step 2: Implement exam API module**

Functions:

- `listExams(params)`
- `createExam(payload)`
- `getExam(id)`
- `updateExam(id, payload)`
- `removeExam(id)`
- `updateExamClasses(id, classIds)`
- `updateExamSubjects(id, subjects)`

- [ ] **Step 3: Implement Exam Center**

The page must include:

- Exam list.
- Keyword, type, term, and status filters.
- Create exam wizard entry button.
- Row actions: detail, score entry, score import, statistics.
- Success after wizard navigates to `/exam-center/{id}/scores` by default so teachers continue directly to score entry.

- [ ] **Step 4: Implement four-step exam wizard**

Wizard state:

```ts
interface ExamWizardState {
  basic: { name: string; exam_type: string; term: string; remark: string }
  class_ids: number[]
  subjects: Array<{
    course_id: number | null
    full_score: string
    pass_score: string
    excellent_score: string
    exam_date?: string
    remark: string
  }>
}
```

Client-side validation:

- Name required.
- At least one class.
- At least one subject.
- Every subject has course, full score, pass score, excellent score.
- `0 <= pass_score <= excellent_score <= full_score`.
- Duplicate course selection is blocked before submit.

- [ ] **Step 5: Implement Exam Detail**

Show:

- Basic exam fields.
- Participating classes.
- Subjects with thresholds and dates.
- Score entry status summary.
- Primary actions: `录入成绩`, `导入成绩`, `查看统计`.

- [ ] **Step 6: Implement Score Entry page**

The top area keeps these controls visible:

- Exam name and term.
- Class filter.
- Subject filter.
- View mode segmented control: `聚焦录入` and `整场总览`.

Table behavior:

- Focused mode filters by class and subject.
- Whole-exam mode renders students as rows and subjects as columns.
- Normal score input is numeric.
- Status selector values: `normal`, `absent`, `deferred`, `cheating`, `exempt`.
- Bulk save calls `PUT /exams/{id}/scores`.
- Failed cells are highlighted by matching `exam_student_id + exam_subject_id`.
- Failure detail text appears next to or below the affected cell.

- [ ] **Step 7: Implement score import dialog**

Dialog actions:

- Download template from `GET /exams/{id}/score-template`.
- Upload Excel file to `POST /exams/{id}/scores/import`.
- Show success count, failure count, status, and row-level errors.
- Link to `/imports/{batch_id}` when a batch id is returned.

- [ ] **Step 8: Run exam and score tests**

Run:

```bash
cd frontend
npm run test -- exam-workflow.spec.ts score-entry.spec.ts
```

Expected:

```text
2 passed
```

- [ ] **Step 9: Commit**

```bash
git add frontend
git commit -m "feat: add exam and score workflows"
```

## Task 12: Frontend Statistics, Import Records, Dashboard, And Account Settings

**Files:**
- Create: `frontend/src/api/statistics.ts`
- Create: `frontend/src/api/imports.ts`
- Create: `frontend/src/api/dashboard.ts`
- Create: `frontend/src/components/dashboard/MetricCard.vue`
- Create: `frontend/src/components/dashboard/TodaySchedule.vue`
- Create: `frontend/src/components/dashboard/RecentExams.vue`
- Create: `frontend/src/components/dashboard/ScoreOverviewCard.vue`
- Create: `frontend/src/components/dashboard/ClassAverageTrend.vue`
- Create: `frontend/src/components/imports/ImportErrorTable.vue`
- Modify: `frontend/src/views/DashboardView.vue`
- Modify: `frontend/src/views/ExamStatisticsView.vue`
- Modify: `frontend/src/views/ImportRecordsView.vue`
- Modify: `frontend/src/views/ImportDetailView.vue`
- Modify: `frontend/src/views/AccountSettingsView.vue`
- Test: `frontend/tests/dashboard.spec.ts`
- Test: `frontend/tests/import-records.spec.ts`

- [ ] **Step 1: Write dashboard component tests**

```ts
// frontend/tests/dashboard.spec.ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ScoreOverviewCard from '../src/components/dashboard/ScoreOverviewCard.vue'

describe('score overview card', () => {
  it('renders required score overview metrics and abnormal distribution labels', () => {
    const wrapper = mount(ScoreOverviewCard, {
      props: {
        overview: {
          average_score: '82.50',
          highest_score: '100.00',
          lowest_score: '32.00',
          abnormal_count: 3,
          total_count: 40,
          low_score_warning: { count: 4, percentage: '10.00' },
          failing: { count: 6, percentage: '15.00' },
          absent: { count: 2, percentage: '5.00' },
          cheating: { count: 1, percentage: '2.50' },
        },
      },
    })
    expect(wrapper.text()).toContain('平均分')
    expect(wrapper.text()).toContain('最高分')
    expect(wrapper.text()).toContain('最低分')
    expect(wrapper.text()).toContain('异常状态分布')
  })
})
```

- [ ] **Step 2: Write import records tests**

```ts
// frontend/tests/import-records.spec.ts
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'
import ImportErrorTable from '../src/components/imports/ImportErrorTable.vue'

describe('import error table', () => {
  it('renders row level error fields', () => {
    const wrapper = mount(ImportErrorTable, {
      props: {
        errors: [{ id: 1, row_number: 3, field: 'student_no', raw_value: 'S001', reason: '学号重复' }],
      },
      global: { stubs: ['el-table', 'el-table-column'] },
    })
    expect(wrapper.text()).toContain('student_no')
    expect(wrapper.text()).toContain('学号重复')
  })
})
```

- [ ] **Step 3: Implement Dashboard**

Dashboard layout:

- Top metric cards: class count, student count, course count, pending score count.
- Today's schedule.
- Recent exams.
- Score overview for latest relevant exam.
- Class average trend.
- Quick actions: create exam, import students, enter scores, view statistics.

Visual constraints:

- Sidebar width stays around `212px`.
- Content starts close to sidebar.
- Card gaps are `8-12px`.
- Cards use radius around `8px`.
- Metric icons use low-saturation teal, blue, indigo, amber, purple, and green.
- No dark sidebar, no high-saturation gradient metric blocks, no one-note palette.

`ScoreOverviewCard.vue` must use a two-part vertical layout:

- Upper metric block with average, highest, lowest, abnormal count.
- Lower abnormal distribution block with title, donut chart with total count in center, and low-score warning, failing, absent, cheating count/percentage rows.

- [ ] **Step 4: Implement Exam Statistics page**

The page must call backend statistics APIs and never recalculate rules locally.

Controls:

- Included status multi-select with default `normal`.
- Ranking type: total or subject.
- Subject select when ranking or segment type is subject.
- Class filter.

Sections:

- Core indicators.
- Class comparison.
- Subject comparison.
- Score segments.
- Rankings.
- Absent, deferred, cheating, exempt lists.
- Missing score list.

- [ ] **Step 5: Implement Import Records pages**

List columns:

- Import type.
- Target object.
- File name.
- Status.
- Success count.
- Failure count.
- Import time.

Detail page:

- Batch metadata.
- Row-level errors table with row number, field, raw value, reason.
- Link back to original workflow when `target_class_id` or `target_exam_id` is present.

- [ ] **Step 6: Implement Account Settings**

Show current teacher account information from `GET /auth/me`:

- Display name.
- Username.
- Email.
- Phone.
- Status.

The first version can be read-only unless profile update is added to the backend in a later plan.

- [ ] **Step 7: Run dashboard and import tests**

Run:

```bash
cd frontend
npm run test -- dashboard.spec.ts import-records.spec.ts
```

Expected:

```text
2 passed
```

- [ ] **Step 8: Commit**

```bash
git add frontend
git commit -m "feat: add dashboard statistics and import review"
```

## Task 13: End-To-End Verification, Visual Review, And Production Build

**Files:**
- Create: `frontend/playwright.config.ts`
- Create: `frontend/e2e/grade-manager.spec.ts`
- Modify: `README.md`

- [ ] **Step 1: Write Playwright workflow test**

```ts
// frontend/e2e/grade-manager.spec.ts
import { expect, test } from '@playwright/test'

test('teacher can follow the exam-driven workflow', async ({ page }) => {
  await page.goto('/login')
  await page.getByLabel('用户名').fill('teacher1')
  await page.getByLabel('密码').fill('strong-password')
  await page.getByRole('button', { name: '登录' }).click()
  await expect(page.getByText('仪表盘')).toBeVisible()

  await page.getByRole('link', { name: '考试中心' }).click()
  await expect(page.getByText('创建考试')).toBeVisible()
})

test('dashboard layout remains compact on desktop widths', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/dashboard')
  const sidebar = page.locator('[data-testid="app-sidebar"]')
  await expect(sidebar).toHaveCSS('width', /20[0-9]px|21[0-9]px|220px/)
  await expect(page.getByText('异常状态分布')).toBeVisible()
})
```

- [ ] **Step 2: Configure Playwright**

```ts
// frontend/playwright.config.ts
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://127.0.0.1:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium-desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'chromium-notebook', use: { viewport: { width: 1280, height: 800 } } },
  ],
})
```

- [ ] **Step 3: Run full backend verification**

Run:

```bash
cd backend
uv run pytest -v
```

Expected:

```text
passed
```

The final line must show zero failures.

- [ ] **Step 4: Run frontend unit tests and build**

Run:

```bash
cd frontend
npm run test
npm run build
```

Expected:

```text
passed
✓ built
```

- [ ] **Step 5: Run local app for visual review**

Terminal 1:

```bash
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Terminal 2:

```bash
cd frontend
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 npm run dev -- --host 127.0.0.1
```

Terminal 3:

```bash
cd frontend
npm run test:e2e
```

Expected:

```text
2 passed
```

- [ ] **Step 6: Manual visual checklist**

Verify these screens at `1440x900` and `1280x800`:

- Login and register forms fit without overlap.
- Dashboard has compact sidebar-to-content spacing.
- Dashboard metric cards do not use high-saturation gradients.
- Score overview card contains average score, highest score, lowest score, abnormal count, abnormal distribution title, donut chart center total, low-score warning, failing, absent, and cheating rows.
- Classes And Students page shows class and student workflows together.
- Courses And Schedule page uses two tabs.
- Exam wizard shows four steps and validates threshold order.
- Score entry focused mode and whole-exam mode both fit without horizontal text overlap.
- Failed score cells show visible highlight and readable failure detail.
- Import result shows success and failure counts with row-level errors.
- Statistics status filter reloads data through API calls.

- [ ] **Step 7: Update README**

`README.md` must include:

````markdown
# Grade Manager

Teacher grade management system with FastAPI backend and Vue 3 frontend.

## Development

```bash
docker compose up -d mysql
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
cd backend && uv run pytest -v
cd frontend && npm run test && npm run build
```
````

- [ ] **Step 8: Commit**

```bash
git add README.md frontend
git commit -m "test: add end-to-end verification"
```

## Cross-Cutting Review Checklist

Before marking the implementation complete, verify:

- All business APIs require JWT except `/auth/register`, `/auth/login`, and `/health`.
- Every business query is scoped to `current_teacher.id`.
- Student imports write valid rows and record invalid rows.
- Score imports resolve through `exam_students`, not current `students.class_id`.
- Exam roster refresh after scoring is a merge, not a destructive rebuild.
- Scores never accept direct `student_id` or `class_id`.
- Statistics default to `included_statuses=normal`.
- Abnormal and missing counts are always visible separately.
- Frontend score filters are presentation state; backend owns statistics rules.
- `401` clears session and redirects to `/login`.
- `409` duplicate conflicts show near relevant form fields where possible.
- `422` validation details preserve row, field, raw value, and reason where available.
- Dashboard follows the fifth compact preview direction without copying preview HTML into production.

## Self-Review Against Specs

Spec coverage:

- Authentication and JWT expiration are covered by Tasks 3 and 9.
- Teacher data isolation is covered by Tasks 3, 4, 5, 6, 7, and the cross-cutting checklist.
- Data models, soft deletion, and constraints are covered by Tasks 2 through 5.
- Student import behavior is covered by Task 7 and frontend display by Task 10.
- Schedule CRUD and dashboard use are covered by Tasks 4, 8, 10, and 12.
- Exam setup, class associations, subject thresholds, and roster snapshots are covered by Task 5.
- Score entry, abnormal statuses, and item-level errors are covered by Tasks 6 and 11.
- Score import and import records are covered by Tasks 7, 11, and 12.
- Statistics rules and included statuses are covered by Tasks 8 and 12.
- Dashboard API and visual requirements are covered by Tasks 8, 12, and 13.
- Frontend navigation, layout, and exam-driven workflow are covered by Tasks 9 through 13.

Placeholder scan:

- The plan avoids `TBD`, empty `TODO`, and "implement later" work.
- Each task has concrete files, behavior, verification commands, expected results, and commit commands.

Type consistency:

- Backend score identifiers are consistently `exam_student_id` and `exam_subject_id`.
- Frontend score cell failure matching uses `exam_student_id + exam_subject_id`.
- Import batch fields use `success_count`, `failed_count`, and `status` consistently.
- Exam subject thresholds use `full_score`, `pass_score`, and `excellent_score` consistently.
