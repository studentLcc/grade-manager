from __future__ import annotations

import json

from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Class, Student, Teacher
from app.modules.imports.service import (
    create_import_batch,
    finalize_import_batch,
    record_import_error,
)
from app.modules.imports.workbook import ImportWorkbookError, load_import_workbook

REQUIRED_COLUMNS = {"student_no", "name"}
OPTIONAL_COLUMNS = {"gender", "status", "remark"}
VALID_STATUSES = {"active", "inactive", "archived"}


def import_students(
    db: Session,
    teacher: Teacher,
    file: UploadFile,
    target_class_id: int,
    update_existing: bool,
) -> dict[str, object]:
    target_class_owned = _class_owned(db, teacher, target_class_id)
    batch = create_import_batch(
        db,
        teacher,
        import_type="students",
        file_name=file.filename or "",
        target_class_id=target_class_id if target_class_owned else None,
    )
    db.commit()
    if not target_class_owned:
        record_import_error(db, batch, None, "target_class_id", target_class_id, "班级不存在")
        finalize_import_batch(batch, 0, 1)
        db.commit()
        return _result(batch)

    success_count = 0
    failed_count = 0
    seen_student_numbers: set[str] = set()
    existing_students = {
        student.student_no: student
        for student in db.scalars(select(Student).where(Student.teacher_id == teacher.id)).all()
    }

    try:
        workbook = load_import_workbook(file)
    except ImportWorkbookError as exc:
        return _fail_batch(db, batch, "file", None, exc.reason)
    worksheet = workbook.active
    headers = _headers(worksheet[1])
    missing = REQUIRED_COLUMNS - set(headers)
    if missing:
        for field in sorted(missing):
            record_import_error(db, batch, 1, field, None, "缺少必填列")
            failed_count += 1
        finalize_import_batch(batch, success_count, failed_count)
        db.commit()
        return _result(batch)

    for row_number, row in _data_rows(worksheet, headers):
        student_no = _clean(row.get("student_no"))
        name = _clean(row.get("name"))
        gender = _clean(row.get("gender"))
        status = _clean(row.get("status")) or "active"
        if not student_no:
            record_import_error(db, batch, row_number, "student_no", row.get("student_no"), "学号不能为空", _raw(row))
            failed_count += 1
            continue
        if student_no in seen_student_numbers:
            record_import_error(db, batch, row_number, "student_no", student_no, "同一文件中学号重复", _raw(row))
            failed_count += 1
            continue
        seen_student_numbers.add(student_no)
        if not name:
            record_import_error(db, batch, row_number, "name", row.get("name"), "姓名不能为空", _raw(row))
            failed_count += 1
            continue
        validation_error = _validate_row(student_no, name, gender, status)
        if validation_error is not None:
            field, reason = validation_error
            record_import_error(db, batch, row_number, field, row.get(field), reason, _raw(row))
            failed_count += 1
            continue

        existing = existing_students.get(student_no)
        if existing is not None and not update_existing:
            record_import_error(db, batch, row_number, "student_no", student_no, "学号已存在", _raw(row))
            failed_count += 1
            continue

        if existing is None:
            student = Student(
                teacher_id=teacher.id,
                class_id=target_class_id,
                student_no=student_no,
                name=name,
                gender=gender,
                status=status,
                remark=_clean(row.get("remark")),
            )
            db.add(student)
            existing_students[student_no] = student
        else:
            existing.name = name
            existing.gender = gender
            existing.class_id = target_class_id
            existing.status = status
            existing.remark = _clean(row.get("remark"))
        success_count += 1

    finalize_import_batch(batch, success_count, failed_count)
    return _commit_or_fail(db, batch)


def _class_owned(db: Session, teacher: Teacher, class_id: int) -> bool:
    return bool(db.scalar(select(Class.id).where(Class.id == class_id, Class.teacher_id == teacher.id)))


def _headers(header_row) -> dict[str, int]:
    return {
        str(cell.value).strip(): index
        for index, cell in enumerate(header_row)
        if cell.value is not None and str(cell.value).strip() in REQUIRED_COLUMNS | OPTIONAL_COLUMNS
    }


def _data_rows(worksheet, headers: dict[str, int]):
    for index, cells in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
        if all(value is None or str(value).strip() == "" for value in cells):
            continue
        yield index, {field: cells[position] if position < len(cells) else None for field, position in headers.items()}


def _clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def _raw(row: dict[str, object]) -> str:
    return json.dumps(row, ensure_ascii=False, default=str)


def _result(batch) -> dict[str, object]:
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "success_count": batch.success_count,
        "failed_count": batch.failed_count,
        "error_summary": batch.error_summary,
    }


def _validate_row(student_no: str, name: str, gender: str, status: str) -> tuple[str, str] | None:
    if len(student_no) > 50:
        return "student_no", "学号不能超过 50 个字符"
    if len(name) > 100:
        return "name", "姓名不能超过 100 个字符"
    if gender and len(gender) > 20:
        return "gender", "性别不能超过 20 个字符"
    if status not in VALID_STATUSES:
        return "status", "学生状态不支持"
    return None


def _fail_batch(
    db: Session,
    batch,
    field: str | None,
    raw_value: object,
    reason: str,
) -> dict[str, object]:
    record_import_error(db, batch, None, field, raw_value, reason)
    finalize_import_batch(batch, 0, 1)
    db.commit()
    return _result(batch)


def _commit_or_fail(db: Session, batch) -> dict[str, object]:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        batch = db.merge(batch)
        record_import_error(db, batch, None, None, None, "数据库写入失败")
        finalize_import_batch(batch, 0, 1)
        db.commit()
    return _result(batch)
