from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.models import Teacher
from app.modules.exams.schemas import (
    ExamClassesUpdate,
    ExamCreate,
    ExamRead,
    ExamSubjectsUpdate,
    ExamUpdate,
    ScoreSaveRequest,
    ScoreSheetRead,
)
from app.modules.exams.service import (
    create_exam,
    get_exam,
    get_score_sheet,
    save_scores,
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


@router.put("/{exam_id}/classes", response_model=ExamRead)
def update_classes(
    payload: ExamClassesUpdate,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(update_exam_classes(db, current_teacher, exam_id, payload))


@router.put("/{exam_id}/subjects", response_model=ExamRead)
def update_subjects(
    payload: ExamSubjectsUpdate,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return serialize_exam(update_exam_subjects(db, current_teacher, exam_id, payload))


@router.get("/{exam_id}/score-sheet", response_model=ScoreSheetRead)
def score_sheet(
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_score_sheet(db, current_teacher, exam_id)


@router.put("/{exam_id}/scores")
def put_scores(
    payload: ScoreSaveRequest,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, int]:
    return save_scores(db, current_teacher, exam_id, payload)
