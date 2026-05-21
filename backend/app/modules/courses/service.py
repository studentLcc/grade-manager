from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import paginate
from app.models import Course, Teacher
from app.modules.courses.schemas import CourseCreate, CourseUpdate


def _ensure_unique_course_name(
    db: Session,
    teacher: Teacher,
    course_name: str,
    exclude_id: int | None = None,
) -> None:
    query = select(Course.id).where(
        Course.teacher_id == teacher.id,
        Course.course_name == course_name,
    )
    if exclude_id is not None:
        query = query.where(Course.id != exclude_id)
    if db.scalar(query) is not None:
        raise AppError(409, "DUPLICATE_RESOURCE", "课程名称已存在")


def list_courses(
    db: Session,
    teacher: Teacher,
    page: int,
    page_size: int,
    keyword: str | None = None,
    status: str | None = None,
) -> tuple[list[Course], int]:
    query = select(Course).where(Course.teacher_id == teacher.id)
    if keyword:
        query = query.where(Course.course_name.like(f"%{keyword}%"))
    query = query.where(Course.status == (status or "active"))
    query = query.order_by(Course.id.desc())
    return paginate(db, query, page, page_size)


def get_course(db: Session, teacher: Teacher, course_id: int) -> Course:
    course = db.scalar(select(Course).where(Course.id == course_id, Course.teacher_id == teacher.id))
    if course is None:
        raise AppError(404, "NOT_FOUND", "课程不存在")
    return course


def create_course(db: Session, teacher: Teacher, payload: CourseCreate) -> Course:
    _ensure_unique_course_name(db, teacher, payload.course_name)
    course = Course(teacher_id=teacher.id, **payload.model_dump())
    db.add(course)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "DUPLICATE_RESOURCE", "课程名称已存在") from exc
    db.refresh(course)
    return course


def update_course(db: Session, teacher: Teacher, course_id: int, payload: CourseUpdate) -> Course:
    course = get_course(db, teacher, course_id)
    data = payload.model_dump(exclude_unset=True)
    if "course_name" in data:
        _ensure_unique_course_name(db, teacher, data["course_name"], exclude_id=course_id)
    for field, value in data.items():
        setattr(course, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "DUPLICATE_RESOURCE", "课程名称已存在") from exc
    db.refresh(course)
    return course


def delete_course(db: Session, teacher: Teacher, course_id: int) -> Course:
    course = get_course(db, teacher, course_id)
    course.status = "inactive"
    db.commit()
    db.refresh(course)
    return course
