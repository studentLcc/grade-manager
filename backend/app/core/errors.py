from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
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


def _format_validation_field(location: tuple[Any, ...]) -> str | None:
    parts = [str(part) for part in location if part not in ("body", "query", "path")]
    return ".".join(parts) if parts else None


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        ErrorDetail(
            field=_format_validation_field(tuple(error.get("loc", ()))),
            value=str(error["input"]) if "input" in error and error["input"] is not None else None,
            reason=str(error.get("msg", "字段校验失败")),
        ).model_dump(exclude_none=True)
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "请求参数校验失败",
            "details": details,
        },
    )
