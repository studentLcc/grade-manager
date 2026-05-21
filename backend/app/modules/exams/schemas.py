from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.errors import AppError, ErrorDetail
from app.core.status import ResourceStatus


class ExamSubjectCreate(BaseModel):
    course_id: int = Field(gt=0)
    full_score: Decimal
    pass_score: Decimal
    excellent_score: Decimal
    exam_date: date | None = None
    remark: str | None = None


class ExamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    exam_type: str | None = Field(default=None, max_length=50)
    term: str | None = Field(default=None, max_length=50)
    remark: str | None = None
    class_ids: list[int]
    subjects: list[ExamSubjectCreate]

    @model_validator(mode="after")
    def validate_exam(self) -> "ExamCreate":
        validate_classes_and_subjects(self.class_ids, self.subjects)
        return self


class ExamUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    exam_type: str | None = Field(default=None, max_length=50)
    term: str | None = Field(default=None, max_length=50)
    status: ResourceStatus | None = None
    remark: str | None = None


class ExamClassesUpdate(BaseModel):
    class_ids: list[int]

    @model_validator(mode="after")
    def validate_classes(self) -> "ExamClassesUpdate":
        if not self.class_ids:
            raise AppError(422, "VALIDATION_ERROR", "考试至少需要一个班级")
        return self


class ExamSubjectUpdateItem(BaseModel):
    id: int | None = Field(default=None, gt=0)
    course_id: int = Field(gt=0)
    full_score: Decimal
    pass_score: Decimal
    excellent_score: Decimal
    status: ResourceStatus | None = None
    exam_date: date | None = None
    remark: str | None = None


class ExamSubjectsUpdate(BaseModel):
    subjects: list[ExamSubjectUpdateItem]

    @model_validator(mode="after")
    def validate_subjects(self) -> "ExamSubjectsUpdate":
        if not self.subjects:
            raise AppError(422, "VALIDATION_ERROR", "考试至少需要一个科目")
        validate_thresholds(self.subjects)
        return self


class ScoreSaveItem(BaseModel):
    exam_student_id: int = Field(gt=0)
    exam_subject_id: int = Field(gt=0)
    score: Decimal | None = None
    score_status: str = Field(default="normal", max_length=20)
    remark: str | None = None


class ScoreSaveRequest(BaseModel):
    items: list[ScoreSaveItem]


class ExamClassRead(BaseModel):
    id: int
    name: str


class ExamSubjectRead(BaseModel):
    id: int
    course_id: int
    course_name: str | None
    full_score: Decimal
    pass_score: Decimal | None
    excellent_score: Decimal | None
    exam_date: date | None
    status: str
    remark: str | None

    model_config = {"from_attributes": True}


class ExamRead(BaseModel):
    id: int
    name: str
    exam_type: str | None
    term: str | None
    status: str
    remark: str | None
    classes: list[ExamClassRead]
    subjects: list[ExamSubjectRead]


class ScoreSheetStudent(BaseModel):
    exam_student_id: int
    student_id: int
    class_id: int
    student_no: str
    name: str
    status: str


class ScoreSheetSubject(BaseModel):
    exam_subject_id: int
    course_id: int
    course_name: str | None
    full_score: Decimal
    pass_score: Decimal | None
    excellent_score: Decimal | None
    exam_date: date | None
    status: str


class ScoreSheetRead(BaseModel):
    exam_id: int
    students: list[ScoreSheetStudent]
    subjects: list[ScoreSheetSubject]


def validate_classes_and_subjects(class_ids: list[int], subjects: list[Any]) -> None:
    if not class_ids:
        raise AppError(422, "VALIDATION_ERROR", "考试至少需要一个班级")
    if not subjects:
        raise AppError(422, "VALIDATION_ERROR", "考试至少需要一个科目")
    validate_thresholds(subjects)


def validate_thresholds(subjects: list[Any]) -> None:
    for subject in subjects:
        if subject.pass_score < 0 or subject.excellent_score < 0 or subject.full_score < 0:
            raise AppError(422, "VALIDATION_ERROR", "分数阈值不能为负数")
        if subject.pass_score > subject.excellent_score or subject.excellent_score > subject.full_score:
            raise AppError(
                422,
                "VALIDATION_ERROR",
                "分数阈值必须满足 0 <= 及格分 <= 优秀分 <= 满分",
                [ErrorDetail(field="subjects.pass_score", reason="分数阈值顺序错误")],
            )
