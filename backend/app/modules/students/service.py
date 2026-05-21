from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import paginate
from app.models import Class, Student, Teacher
from app.modules.students.schemas import StudentCreate, StudentUpdate


def _ensure_class_belongs_to_teacher(db: Session, teacher: Teacher, class_id: int | None) -> None:
    if class_id is None:
        return
    exists = db.scalar(select(Class.id).where(Class.id == class_id, Class.teacher_id == teacher.id))
    if exists is None:
        raise AppError(404, "NOT_FOUND", "班级不存在")


def _ensure_unique_student_no(
    db: Session,
    teacher: Teacher,
    student_no: str,
    exclude_id: int | None = None,
) -> None:
    query = select(Student.id).where(
        Student.teacher_id == teacher.id,
        Student.student_no == student_no,
    )
    if exclude_id is not None:
        query = query.where(Student.id != exclude_id)
    if db.scalar(query) is not None:
        raise AppError(409, "DUPLICATE_RESOURCE", "学号已存在")


def list_students(
    db: Session,
    teacher: Teacher,
    page: int,
    page_size: int,
    keyword: str | None = None,
    status: str | None = None,
    class_id: int | None = None,
) -> tuple[list[Student], int]:
    query = select(Student).where(Student.teacher_id == teacher.id)
    if keyword:
        query = query.where(
            Student.name.like(f"%{keyword}%") | Student.student_no.like(f"%{keyword}%")
        )
    query = query.where(Student.status == (status or "active"))
    if class_id is not None:
        query = query.where(Student.class_id == class_id)
    query = query.order_by(Student.id.desc())
    return paginate(db, query, page, page_size)


def get_student(db: Session, teacher: Teacher, student_id: int) -> Student:
    student = db.scalar(select(Student).where(Student.id == student_id, Student.teacher_id == teacher.id))
    if student is None:
        raise AppError(404, "NOT_FOUND", "学生不存在")
    return student


def create_student(db: Session, teacher: Teacher, payload: StudentCreate) -> Student:
    _ensure_class_belongs_to_teacher(db, teacher, payload.class_id)
    _ensure_unique_student_no(db, teacher, payload.student_no)
    student = Student(teacher_id=teacher.id, **payload.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "DUPLICATE_RESOURCE", "学号已存在") from exc
    db.refresh(student)
    return student


def update_student(db: Session, teacher: Teacher, student_id: int, payload: StudentUpdate) -> Student:
    student = get_student(db, teacher, student_id)
    data = payload.model_dump(exclude_unset=True)
    if "class_id" in data:
        _ensure_class_belongs_to_teacher(db, teacher, data["class_id"])
    if "student_no" in data:
        _ensure_unique_student_no(db, teacher, data["student_no"], exclude_id=student_id)
    for field, value in data.items():
        setattr(student, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "DUPLICATE_RESOURCE", "学号已存在") from exc
    db.refresh(student)
    return student


def delete_student(db: Session, teacher: Teacher, student_id: int) -> Student:
    student = get_student(db, teacher, student_id)
    student.status = "inactive"
    db.commit()
    db.refresh(student)
    return student
