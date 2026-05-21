from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.errors import AppError
from app.core.security import decode_access_token
from app.models import Teacher

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_current_teacher(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Teacher:
    if not token:
        raise AppError(401, "UNAUTHORIZED", "登录已过期，请重新登录")
    payload = decode_access_token(token)
    teacher_id = payload.get("sub")
    if not teacher_id:
        raise AppError(401, "UNAUTHORIZED", "登录已过期，请重新登录")
    try:
        teacher_pk = int(teacher_id)
    except ValueError as exc:
        raise AppError(401, "UNAUTHORIZED", "登录已过期，请重新登录") from exc
    teacher = db.get(Teacher, teacher_pk)
    if teacher is None or teacher.status != "active":
        raise AppError(401, "UNAUTHORIZED", "登录已过期，请重新登录")
    return teacher
