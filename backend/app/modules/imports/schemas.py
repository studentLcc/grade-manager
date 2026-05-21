from datetime import datetime

from pydantic import BaseModel


class ImportResult(BaseModel):
    batch_id: int
    status: str
    success_count: int
    failed_count: int
    error_summary: str | None


class ImportBatchRead(BaseModel):
    id: int
    import_type: str
    target_class_id: int | None
    target_class_name: str | None = None
    target_exam_id: int | None
    target_exam_name: str | None = None
    target_exam_subject_id: int | None
    target_exam_subject_name: str | None = None
    file_name: str
    status: str
    success_count: int
    failed_count: int
    error_summary: str | None
    created_at: datetime
    updated_at: datetime


class ImportErrorRead(BaseModel):
    id: int
    batch_id: int
    row_number: int | None
    field: str | None
    raw_value: str | None
    reason: str
    raw_data: str | None
    created_at: datetime
