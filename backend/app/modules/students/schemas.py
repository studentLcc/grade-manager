from datetime import datetime

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.status import ResourceStatus


class StudentCreate(BaseModel):
    class_id: int | None = Field(default=None, gt=0)
    student_no: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=100)
    gender: str | None = Field(default=None, max_length=20)
    remark: str | None = None


class StudentUpdate(BaseModel):
    class_id: int | None = Field(default=None, gt=0)
    student_no: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    gender: str | None = Field(default=None, max_length=20)
    status: ResourceStatus | None = None
    remark: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ("student_no", "name", "status"):
                if field in data and data[field] is None:
                    raise ValueError(f"{field} 不能为空")
        return data


class StudentRead(BaseModel):
    id: int
    teacher_id: int
    class_id: int | None
    student_no: str
    name: str
    gender: str | None
    status: str
    remark: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
