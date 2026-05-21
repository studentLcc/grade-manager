from datetime import datetime

from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.core.status import ResourceStatus


class ClassCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    grade: str | None = Field(default=None, max_length=50)
    academic_year: str | None = Field(default=None, max_length=20)
    remark: str | None = None


class ClassUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    grade: str | None = Field(default=None, max_length=50)
    academic_year: str | None = Field(default=None, max_length=20)
    status: ResourceStatus | None = None
    remark: str | None = None

    @model_validator(mode="before")
    @classmethod
    def reject_null_required_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for field in ("name", "status"):
                if field in data and data[field] is None:
                    raise ValueError(f"{field} 不能为空")
        return data


class ClassRead(BaseModel):
    id: int
    teacher_id: int
    name: str
    grade: str | None
    academic_year: str | None
    status: str
    remark: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
