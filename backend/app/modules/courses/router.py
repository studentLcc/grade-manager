from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.core.pagination import Page, PageParams
from app.core.status import ResourceStatus
from app.models import Course, Teacher
from app.modules.courses.schemas import CourseCreate, CourseRead, CourseUpdate
from app.modules.courses.service import (
    create_course,
    delete_course,
    get_course,
    list_courses,
    update_course,
)

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=Page[CourseRead])
def list_(
    params: PageParams = Depends(),
    keyword: str | None = None,
    status: ResourceStatus | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    items, total = list_courses(db, current_teacher, params.page, params.page_size, keyword, status)
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}


@router.post("", response_model=CourseRead, status_code=201)
def create(
    payload: CourseCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Course:
    return create_course(db, current_teacher, payload)


@router.get("/{course_id}", response_model=CourseRead)
def get(
    course_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Course:
    return get_course(db, current_teacher, course_id)


@router.patch("/{course_id}", response_model=CourseRead)
def update(
    payload: CourseUpdate,
    course_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Course:
    return update_course(db, current_teacher, course_id, payload)


@router.delete("/{course_id}", response_model=CourseRead)
def delete(
    course_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Course:
    return delete_course(db, current_teacher, course_id)
