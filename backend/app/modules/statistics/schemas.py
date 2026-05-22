from decimal import Decimal

from pydantic import BaseModel


class StatisticsExamRef(BaseModel):
    id: int
    name: str


class OverallStatistics(BaseModel):
    average_score: Decimal
    highest_score: Decimal
    lowest_score: Decimal
    pass_rate: Decimal
    excellent_rate: Decimal


class ComparisonItem(BaseModel):
    id: int
    name: str
    average_score: Decimal
    highest_score: Decimal
    lowest_score: Decimal
    pass_rate: Decimal
    excellent_rate: Decimal


class StudentListItem(BaseModel):
    exam_student_id: int
    student_id: int
    student_no: str
    name: str
    class_id: int
    class_name: str | None
    exam_subject_id: int | None = None
    course_name: str | None = None


class ExamSummaryRead(BaseModel):
    exam: StatisticsExamRef
    included_statuses: list[str]
    overall: OverallStatistics
    class_comparison: list[ComparisonItem]
    subject_comparison: list[ComparisonItem]
    abnormal_counts: dict[str, int]
    missing_score_count: int
    abnormal_lists: dict[str, list[StudentListItem]]
    missing_score_list: list[StudentListItem]


class RankingItem(BaseModel):
    rank: int
    exam_student_id: int
    student_id: int
    student_no: str
    name: str
    class_id: int
    class_name: str | None
    score: Decimal


class RankingRead(BaseModel):
    exam: StatisticsExamRef
    included_statuses: list[str]
    rank_type: str
    exam_subject_id: int | None
    class_id: int | None
    items: list[RankingItem]


class SegmentItem(BaseModel):
    label: str
    start: Decimal
    end: Decimal
    count: int


class SegmentRead(BaseModel):
    exam: StatisticsExamRef
    included_statuses: list[str]
    type: str
    exam_subject_id: int | None
    step: int
    items: list[SegmentItem]


class StudentHistoryItem(BaseModel):
    exam_id: int
    exam_name: str
    class_id: int
    class_name: str | None
    total_score: Decimal
    average_score: Decimal


class StudentHistoryRead(BaseModel):
    student_id: int
    items: list[StudentHistoryItem]


class ClassOverviewItem(BaseModel):
    exam_id: int
    exam_name: str
    class_id: int
    class_name: str | None
    average_score: Decimal


class ClassOverviewRead(BaseModel):
    class_id: int
    items: list[ClassOverviewItem]
