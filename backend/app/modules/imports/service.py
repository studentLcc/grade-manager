from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import paginate
from app.models import ImportBatch, ImportError as ImportRowError, Teacher

MAX_IMPORT_FILE_NAME_LENGTH = 255
MAX_IMPORT_ERROR_FIELD_LENGTH = 100
MAX_IMPORT_ERROR_RAW_VALUE_LENGTH = 10_000
MAX_IMPORT_ERROR_RAW_DATA_LENGTH = 10_000


def create_import_batch(
    db: Session,
    teacher: Teacher,
    import_type: str,
    file_name: str,
    target_class_id: int | None = None,
    target_exam_id: int | None = None,
    target_exam_subject_id: int | None = None,
) -> ImportBatch:
    batch = ImportBatch(
        teacher_id=teacher.id,
        import_type=import_type,
        target_class_id=target_class_id,
        target_exam_id=target_exam_id,
        target_exam_subject_id=target_exam_subject_id,
        file_name=_bounded_text(file_name, MAX_IMPORT_FILE_NAME_LENGTH) or "",
        status="processing",
        success_count=0,
        failed_count=0,
    )
    db.add(batch)
    db.flush()
    return batch


def record_import_error(
    db: Session,
    batch: ImportBatch,
    row_number: int | None,
    field: str | None,
    raw_value: object,
    reason: str,
    raw_data: str | None = None,
) -> None:
    db.add(
        ImportRowError(
            batch_id=batch.id,
            row_number=row_number,
            field=_bounded_text(field, MAX_IMPORT_ERROR_FIELD_LENGTH),
            raw_value=_bounded_text(
                "" if raw_value is None else str(raw_value),
                MAX_IMPORT_ERROR_RAW_VALUE_LENGTH,
            ),
            reason=reason,
            raw_data=_bounded_text(raw_data, MAX_IMPORT_ERROR_RAW_DATA_LENGTH),
        )
    )


def finalize_import_batch(batch: ImportBatch, success_count: int, failed_count: int) -> None:
    batch.success_count = success_count
    batch.failed_count = failed_count
    if success_count > 0 and failed_count == 0:
        batch.status = "success"
    elif success_count > 0 and failed_count > 0:
        batch.status = "partial_success"
    else:
        batch.status = "failed"
    batch.error_summary = None if failed_count == 0 else f"{failed_count} 行导入失败"


def serialize_import_batch(batch: ImportBatch) -> dict[str, object]:
    target_exam_subject_name = None
    if batch.target_exam_subject is not None and batch.target_exam_subject.course is not None:
        target_exam_subject_name = batch.target_exam_subject.course.course_name
    return {
        "id": batch.id,
        "import_type": batch.import_type,
        "target_class_id": batch.target_class_id,
        "target_class_name": batch.target_class.name if batch.target_class is not None else None,
        "target_exam_id": batch.target_exam_id,
        "target_exam_name": batch.target_exam.name if batch.target_exam is not None else None,
        "target_exam_subject_id": batch.target_exam_subject_id,
        "target_exam_subject_name": target_exam_subject_name,
        "file_name": batch.file_name,
        "status": batch.status,
        "success_count": batch.success_count,
        "failed_count": batch.failed_count,
        "error_summary": batch.error_summary,
        "created_at": batch.created_at,
        "updated_at": batch.updated_at,
    }


def list_import_batches(
    db: Session,
    teacher: Teacher,
    page: int,
    page_size: int,
    import_type: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[dict[str, object]], int]:
    query = select(ImportBatch).where(ImportBatch.teacher_id == teacher.id)
    if import_type:
        query = query.where(ImportBatch.import_type == import_type)
    if status:
        query = query.where(ImportBatch.status == status)
    if keyword:
        query = query.where(or_(ImportBatch.file_name.like(f"%{keyword}%")))
    query = query.order_by(ImportBatch.id.desc())
    items, total = paginate(db, query, page, page_size)
    return [serialize_import_batch(item) for item in items], total


def get_import_batch(db: Session, teacher: Teacher, batch_id: int) -> dict[str, object]:
    batch = db.scalar(
        select(ImportBatch).where(ImportBatch.id == batch_id, ImportBatch.teacher_id == teacher.id)
    )
    if batch is None:
        raise AppError(404, "NOT_FOUND", "导入批次不存在")
    return serialize_import_batch(batch)


def list_import_errors(
    db: Session,
    teacher: Teacher,
    batch_id: int,
    page: int,
    page_size: int,
) -> tuple[list[ImportRowError], int]:
    if not db.scalar(
        select(ImportBatch.id).where(ImportBatch.id == batch_id, ImportBatch.teacher_id == teacher.id)
    ):
        raise AppError(404, "NOT_FOUND", "导入批次不存在")
    query = (
        select(ImportRowError)
        .where(ImportRowError.batch_id == batch_id)
        .order_by(ImportRowError.row_number, ImportRowError.id)
    )
    return paginate(db, query, page, page_size)


def _bounded_text(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    return value[:max_length]
