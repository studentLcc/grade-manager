from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.models import Teacher
from app.modules.statistics.schemas import (
    ClassOverviewRead,
    ExamSummaryRead,
    RankingRead,
    SegmentRead,
    StudentHistoryRead,
)
from app.modules.statistics.service import (
    get_class_overview,
    get_exam_summary,
    get_rankings,
    get_segments,
    get_student_history,
)

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/exams/{exam_id}/summary", response_model=ExamSummaryRead)
def exam_summary(
    exam_id: int = Path(gt=0),
    included_statuses: str | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_exam_summary(db, current_teacher, exam_id, included_statuses)


@router.get("/exams/{exam_id}/rankings", response_model=RankingRead)
def rankings(
    exam_id: int = Path(gt=0),
    rank_type: str = Query(default="total"),
    exam_subject_id: int | None = Query(default=None, gt=0),
    class_id: int | None = Query(default=None, gt=0),
    included_statuses: str | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_rankings(
        db,
        current_teacher,
        exam_id,
        rank_type,
        exam_subject_id,
        class_id,
        included_statuses,
    )


@router.get("/exams/{exam_id}/segments", response_model=SegmentRead)
def segments(
    exam_id: int = Path(gt=0),
    type: str = Query(default="total"),  # noqa: A002
    step: int = Query(default=10, gt=0),
    exam_subject_id: int | None = Query(default=None, gt=0),
    class_id: int | None = Query(default=None, gt=0),
    included_statuses: str | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_segments(db, current_teacher, exam_id, type, step, exam_subject_id, class_id, included_statuses)


@router.get("/students/{student_id}/history", response_model=StudentHistoryRead)
def student_history(
    student_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_student_history(db, current_teacher, student_id)


@router.get("/classes/{class_id}/overview", response_model=ClassOverviewRead)
def class_overview(
    class_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_class_overview(db, current_teacher, class_id)
