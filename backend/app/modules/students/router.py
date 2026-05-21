from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.core.pagination import Page, PageParams
from app.core.status import ResourceStatus
from app.models import Student, Teacher
from app.modules.students.schemas import StudentCreate, StudentRead, StudentUpdate
from app.modules.students.service import (
    create_student,
    delete_student,
    get_student,
    list_students,
    update_student,
)

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=Page[StudentRead])
def list_(
    params: PageParams = Depends(),
    keyword: str | None = None,
    status: ResourceStatus | None = None,
    class_id: int | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    items, total = list_students(
        db,
        current_teacher,
        params.page,
        params.page_size,
        keyword,
        status,
        class_id,
    )
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}


@router.post("", response_model=StudentRead, status_code=201)
def create(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Student:
    return create_student(db, current_teacher, payload)


@router.get("/{student_id}", response_model=StudentRead)
def get(
    student_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Student:
    return get_student(db, current_teacher, student_id)


@router.patch("/{student_id}", response_model=StudentRead)
def update(
    payload: StudentUpdate,
    student_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Student:
    return update_student(db, current_teacher, student_id, payload)


@router.delete("/{student_id}", response_model=StudentRead)
def delete(
    student_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Student:
    return delete_student(db, current_teacher, student_id)
