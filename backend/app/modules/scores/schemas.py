from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ScoreSaveItem(BaseModel):
    model_config = ConfigDict(extra="allow")

    exam_student_id: int = Field(gt=0)
    exam_subject_id: int = Field(gt=0)
    score: Decimal | None = None
    score_status: str = Field(default="normal", max_length=20)
    remark: str | None = None

    @model_validator(mode="before")
    @classmethod
    def keep_payload_mapping(cls, data: Any) -> Any:
        return data


class ScoreSaveRequest(BaseModel):
    items: list[ScoreSaveItem]


class ScoreFailureItem(BaseModel):
    index: int
    exam_student_id: int | None = None
    exam_subject_id: int | None = None
    reason: str


class ScoreSaveResult(BaseModel):
    success_count: int
    failure_count: int
    failed_items: list[ScoreFailureItem]


class ScoreSheetExam(BaseModel):
    id: int
    name: str
    exam_type: str | None
    term: str | None


class ScoreSheetClass(BaseModel):
    id: int
    name: str


class ScoreSheetSubject(BaseModel):
    exam_subject_id: int
    course_id: int
    course_name: str | None
    full_score: Decimal
    pass_score: Decimal | None
    excellent_score: Decimal | None
    status: str


class ScoreSheetStudent(BaseModel):
    exam_student_id: int
    student_id: int
    class_id: int
    student_no: str
    name: str
    status: str


class ScoreSheetScore(BaseModel):
    exam_student_id: int
    exam_subject_id: int
    score: Decimal | None
    score_status: str
    remark: str | None


class ScoreSheetRead(BaseModel):
    exam: ScoreSheetExam
    classes: list[ScoreSheetClass]
    subjects: list[ScoreSheetSubject]
    students: list[ScoreSheetStudent]
    scores: list[ScoreSheetScore]
