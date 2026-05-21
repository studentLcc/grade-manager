from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import paginate
from app.models import Class, Teacher
from app.modules.classes.schemas import ClassCreate, ClassUpdate


def list_classes(
    db: Session,
    teacher: Teacher,
    page: int,
    page_size: int,
    keyword: str | None = None,
    status: str | None = None,
) -> tuple[list[Class], int]:
    query = select(Class).where(Class.teacher_id == teacher.id)
    if keyword:
        query = query.where(Class.name.like(f"%{keyword}%"))
    query = query.where(Class.status == (status or "active"))
    query = query.order_by(Class.id.desc())
    return paginate(db, query, page, page_size)


def get_class(db: Session, teacher: Teacher, class_id: int) -> Class:
    class_ = db.scalar(select(Class).where(Class.id == class_id, Class.teacher_id == teacher.id))
    if class_ is None:
        raise AppError(404, "NOT_FOUND", "班级不存在")
    return class_


def create_class(db: Session, teacher: Teacher, payload: ClassCreate) -> Class:
    class_ = Class(teacher_id=teacher.id, **payload.model_dump())
    db.add(class_)
    db.commit()
    db.refresh(class_)
    return class_


def update_class(db: Session, teacher: Teacher, class_id: int, payload: ClassUpdate) -> Class:
    class_ = get_class(db, teacher, class_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(class_, field, value)
    db.commit()
    db.refresh(class_)
    return class_


def delete_class(db: Session, teacher: Teacher, class_id: int) -> Class:
    class_ = get_class(db, teacher, class_id)
    class_.status = "inactive"
    db.commit()
    db.refresh(class_)
    return class_
