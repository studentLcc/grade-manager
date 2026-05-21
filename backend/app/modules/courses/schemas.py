from datetime import datetime

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.status import ResourceStatus


class CourseCreate(BaseModel):
    course_name: str = Field(min_length=1, max_length=100)
    remark: str | None = None


class CourseUpdate(BaseModel):
    course_name: str | None = Field(default=None, min_length=1, max_length=100)
    status: ResourceStatus | None = None
    remark: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ("course_name", "status"):
                if field in data and data[field] is None:
                    raise ValueError(f"{field} 不能为空")
        return data


class CourseRead(BaseModel):
    id: int
    teacher_id: int
    course_name: str
    status: str
    remark: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
