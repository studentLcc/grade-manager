from fastapi import APIRouter

from app.modules.auth.router import router as auth_router

api_router = APIRouter(prefix="/api/v1")


@api_router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


api_router.include_router(auth_router)
