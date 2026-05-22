from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.core.pagination import Page, PageParams
from app.core.status import ResourceStatus
from app.models import Teacher
from app.modules.exams.schemas import (
    ExamClassesUpdate,
    ExamCreate,
    ExamRead,
    ExamSubjectsUpdate,
    ExamUpdate,
)
from app.modules.exams.service import (
    create_exam,
    delete_exam,
    get_exam,
    list_exams,
    serialize_exam,
    update_exam,
    update_exam_classes,
    update_exam_subjects,
)

router = APIRouter(prefix="/exams", tags=["exams"])


@router.post("", response_model=ExamRead, status_code=201)
def create(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(create_exam(db, current_teacher, payload))


@router.get("", response_model=Page[ExamRead])
def list_(
    params: PageParams = Depends(),
    keyword: str | None = None,
    exam_type: str | None = None,
    term: str | None = None,
    status: ResourceStatus | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    items, total = list_exams(
        db,
        current_teacher,
        params.page,
        params.page_size,
        keyword,
        exam_type,
        term,
        status,
    )
    return {"items": [serialize_exam(item) for item in items], "total": total, "page": params.page, "page_size": params.page_size}


@router.get("/{exam_id}", response_model=ExamRead)
def get(
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(get_exam(db, current_teacher, exam_id))


@router.patch("/{exam_id}", response_model=ExamRead)
def update(
    payload: ExamUpdate,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(update_exam(db, current_teacher, exam_id, payload))


@router.delete("/{exam_id}", response_model=ExamRead)
def delete(
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(delete_exam(db, current_teacher, exam_id))


@router.patch("/{exam_id}/classes", response_model=ExamRead)
def update_classes(
    payload: ExamClassesUpdate,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(update_exam_classes(db, current_teacher, exam_id, payload))


@router.put("/{exam_id}/classes", response_model=ExamRead)
def put_classes(
    payload: ExamClassesUpdate,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(update_exam_classes(db, current_teacher, exam_id, payload))


@router.patch("/{exam_id}/subjects", response_model=ExamRead)
def update_subjects(
    payload: ExamSubjectsUpdate,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(update_exam_subjects(db, current_teacher, exam_id, payload))


@router.put("/{exam_id}/subjects", response_model=ExamRead)
def put_subjects(
    payload: ExamSubjectsUpdate,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(update_exam_subjects(db, current_teacher, exam_id, payload))
