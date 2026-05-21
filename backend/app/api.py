from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.classes.router import router as classes_router
from app.modules.courses.router import router as courses_router
from app.modules.exams.router import router as exams_router
from app.modules.schedules.router import router as schedules_router
from app.modules.scores.router import router as scores_router
from app.modules.students.router import router as students_router

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth_router)
api_router.include_router(classes_router)
api_router.include_router(students_router)
api_router.include_router(courses_router)
api_router.include_router(schedules_router)
api_router.include_router(exams_router)
api_router.include_router(scores_router)
