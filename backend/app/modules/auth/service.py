from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Teacher
from app.modules.auth.schemas import TeacherLogin, TeacherRegister, TokenResponse


def register_teacher(db: Session, payload: TeacherRegister) -> Teacher:
    existing = db.scalar(select(Teacher).where(Teacher.username == payload.username))
    if existing is not None:
        raise AppError(409, "DUPLICATE_RESOURCE", "用户名已存在")

    teacher = Teacher(
        username=payload.username,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
        email=payload.email,
        phone=payload.phone,
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


def login_teacher(db: Session, payload: TeacherLogin) -> TokenResponse:
    teacher = db.scalar(select(Teacher).where(Teacher.username == payload.username))
    if (
        teacher is None
        or teacher.status != "active"
        or not verify_password(payload.password, teacher.password_hash)
    ):
        raise AppError(401, "UNAUTHORIZED", "用户名或密码错误")

    return TokenResponse(
        access_token=create_access_token(subject=str(teacher.id)),
        teacher=teacher,
    )
