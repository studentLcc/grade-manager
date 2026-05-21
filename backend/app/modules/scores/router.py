from fastapi import APIRouter, Depends, File, Path, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.models import Teacher
from app.modules.imports.schemas import ImportResult
from app.modules.scores.import_service import import_scores
from app.modules.scores.schemas import ScoreSaveRequest, ScoreSaveResult, ScoreSheetRead
from app.modules.scores.service import get_score_sheet, save_scores
from app.modules.scores.template_service import build_score_template

router = APIRouter(prefix="/exams", tags=["scores"])


@router.get("/{exam_id}/score-sheet", response_model=ScoreSheetRead)
def score_sheet(
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_score_sheet(db, current_teacher, exam_id)


@router.put("/{exam_id}/scores", response_model=ScoreSaveResult)
def put_scores(
    payload: ScoreSaveRequest,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return save_scores(db, current_teacher, exam_id, payload)


@router.get("/{exam_id}/score-template")
def score_template(
    exam_id: int = Path(gt=0),
    class_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Response:
    content = build_score_template(db, current_teacher, exam_id, class_id)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="exam-{exam_id}-score-template.xlsx"'},
    )


@router.post("/{exam_id}/scores/import", response_model=ImportResult)
def import_(
    exam_id: int = Path(gt=0),
    overwrite_existing: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return import_scores(db, current_teacher, exam_id, file, overwrite_existing)
