from datetime import datetime, time

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.status import ResourceStatus


class ScheduleCreate(BaseModel):
    class_id: int = Field(gt=0)
    course_id: int = Field(gt=0)
    weekday: int
    period_no: int
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(default=None, max_length=100)
    remark: str | None = None


class ScheduleUpdate(BaseModel):
    class_id: int | None = Field(default=None, gt=0)
    course_id: int | None = Field(default=None, gt=0)
    weekday: int | None = None
    period_no: int | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(default=None, max_length=100)
    status: ResourceStatus | None = None
    remark: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ("class_id", "course_id", "weekday", "period_no", "status"):
                if field in data and data[field] is None:
                    raise ValueError(f"{field} 不能为空")
        return data


class ScheduleRead(BaseModel):
    id: int
    teacher_id: int
    class_id: int
    course_id: int
    weekday: int
    period_no: int
    start_time: time | None
    end_time: time | None
    location: str | None
    status: str
    remark: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
