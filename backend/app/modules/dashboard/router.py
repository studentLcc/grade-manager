from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.models import Teacher
from app.modules.dashboard.schemas import (
    ClassAverageTrendRead,
    DashboardSummaryRead,
    RecentExamRead,
    ScoreOverviewRead,
    TodayScheduleRead,
)
from app.modules.dashboard.service import (
    get_class_average_trend,
    get_dashboard_summary,
    get_recent_exams,
    get_score_overview,
    get_today_schedule,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryRead)
def summary(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_dashboard_summary(db, current_teacher)


@router.get("/today-schedule", response_model=TodayScheduleRead)
def today_schedule(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_today_schedule(db, current_teacher)


@router.get("/recent-exams", response_model=RecentExamRead)
def recent_exams(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_recent_exams(db, current_teacher)


@router.get("/score-overview", response_model=ScoreOverviewRead)
def score_overview(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_score_overview(db, current_teacher)


@router.get("/class-average-trend", response_model=ClassAverageTrendRead)
def class_average_trend(
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_class_average_trend(db, current_teacher)
