from datetime import time
from decimal import Decimal

from pydantic import BaseModel


class DashboardSummaryRead(BaseModel):
    class_count: int
    student_count: int
    course_count: int
    recent_exam_count: int
    pending_score_count: int


class TodayScheduleItem(BaseModel):
    id: int
    class_id: int
    class_name: str | None
    course_id: int
    course_name: str | None
    weekday: int
    period_no: int
    start_time: time | None
    end_time: time | None
    location: str | None


class TodayScheduleRead(BaseModel):
    items: list[TodayScheduleItem]


class RecentExamItem(BaseModel):
    id: int
    name: str
    exam_type: str | None
    term: str | None


class RecentExamRead(BaseModel):
    items: list[RecentExamItem]


class LatestExamRef(BaseModel):
    id: int
    name: str


class ScoreOverviewRead(BaseModel):
    latest_exam: LatestExamRef | None
    average_score: Decimal
    highest_score: Decimal
    lowest_score: Decimal
    abnormal_count: int
    abnormal_distribution: dict[str, int]
    low_score_warning: int
    failing_count: int
    absent_count: int
    cheating_count: int


class ClassAverageTrendItem(BaseModel):
    exam_id: int
    exam_name: str
    class_id: int
    class_name: str | None
    average_score: Decimal


class ClassAverageTrendRead(BaseModel):
    items: list[ClassAverageTrendItem]
