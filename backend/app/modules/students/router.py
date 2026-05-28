from fastapi import APIRouter, Depends, File, Path, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.core.pagination import Page, PageParams
from app.core.status import ResourceStatus
from app.models import Student, Teacher
from app.modules.imports.schemas import ImportResult
from app.modules.students.import_service import import_students
from app.modules.students.schemas import StudentCreate, StudentRead, StudentUpdate
from app.modules.students.service import (
    create_student,
    delete_student,
    get_student,
    list_students,
    update_student,
)
from app.modules.students.template_service import build_student_import_template

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


@router.post("/import", response_model=ImportResult)
def import_(
    target_class_id: int = Query(gt=0),
    update_existing: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return import_students(db, current_teacher, file, target_class_id, update_existing)


@router.get("/import-template")
def import_template(
    _current_teacher: Teacher = Depends(get_current_teacher),
) -> Response:
    content = build_student_import_template()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="student-import-template.xlsx"'},
    )


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
