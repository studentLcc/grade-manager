from fastapi import APIRouter, Depends, File, Path, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.core.pagination import Page, PageParams
from app.models import Teacher
from app.modules.imports.schemas import ImportResult
from app.modules.scores.import_service import import_scores
from app.modules.scores.schemas import ScoreRecordRead, ScoreSaveRequest, ScoreSaveResult, ScoreSheetRead
from app.modules.scores.service import get_score_sheet, list_score_records, save_scores
from app.modules.scores.template_service import build_score_template

router = APIRouter(tags=["scores"])


@router.get("/scores", response_model=Page[ScoreRecordRead])
def list_(
    params: PageParams = Depends(),
    keyword: str | None = None,
    exam_id: int | None = Query(default=None, gt=0),
    class_id: int | None = Query(default=None, gt=0),
    course_id: int | None = Query(default=None, gt=0),
    status: str | None = None,
    score_status: str | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    items, total = list_score_records(
        db,
        current_teacher,
        params.page,
        params.page_size,
        keyword,
        exam_id,
        class_id,
        course_id,
        status,
        score_status,
    )
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}


@router.get("/exams/{exam_id}/score-sheet", response_model=ScoreSheetRead)
def score_sheet(
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_score_sheet(db, current_teacher, exam_id)


@router.put("/exams/{exam_id}/scores", response_model=ScoreSaveResult)
def put_scores(
    payload: ScoreSaveRequest,
    exam_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return save_scores(db, current_teacher, exam_id, payload)


@router.get("/exams/{exam_id}/score-template")
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


@router.post("/exams/{exam_id}/scores/import", response_model=ImportResult)
def import_(
    exam_id: int = Path(gt=0),
    overwrite_existing: bool = False,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return import_scores(db, current_teacher, exam_id, file, overwrite_existing)
