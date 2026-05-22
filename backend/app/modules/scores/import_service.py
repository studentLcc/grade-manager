from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Course, ExamStudent, ExamSubject, Score, Student, Teacher
from app.modules.exams.service import get_active_exam_for_mutation
from app.modules.imports.service import (
    create_import_batch,
    finalize_import_batch,
    record_import_error,
)
from app.modules.imports.workbook import ImportWorkbookError, load_import_workbook

ABNORMAL_SCORE_STATUSES = {"absent", "deferred", "cheating", "exempt"}
RESERVED_COLUMNS = {"student_no", "student_name", "class_name"}
type HeaderColumn = tuple[str, int]


def import_scores(
    db: Session,
    teacher: Teacher,
    exam_id: int,
    file: UploadFile,
    overwrite_existing: bool,
) -> dict[str, object]:
    exam = get_active_exam_for_mutation(db, teacher, exam_id)
    batch = create_import_batch(
        db,
        teacher,
        import_type="scores",
        file_name=file.filename or "",
        target_exam_id=exam.id,
    )
    db.commit()

    students_by_no = {
        student.student_no: exam_student
        for exam_student, student in db.execute(
            select(ExamStudent, Student)
            .join(Student, Student.id == ExamStudent.student_id)
            .where(ExamStudent.exam_id == exam.id)
        ).all()
    }
    subjects_by_name = {
        course.course_name: subject
        for subject, course in db.execute(
            select(ExamSubject, Course)
            .join(Course, Course.id == ExamSubject.course_id)
            .where(ExamSubject.exam_id == exam.id, ExamSubject.status == "active")
        ).all()
    }
    existing_scores = {
        (score.exam_student_id, score.exam_subject_id): score
        for score in db.scalars(
            select(Score)
            .join(ExamStudent, ExamStudent.id == Score.exam_student_id)
            .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
            .where(ExamStudent.exam_id == exam.id, ExamSubject.exam_id == exam.id)
        )
    }

    try:
        workbook = load_import_workbook(file)
    except ImportWorkbookError as exc:
        return _fail_batch(db, batch, "file", None, exc.reason)
    worksheet = workbook.active
    headers = _headers(worksheet[1])
    header_names = {name for name, _ in headers}
    success_count = 0
    failed_count = 0
    seen_keys: set[tuple[int, int]] = set()

    if "student_no" not in header_names:
        record_import_error(db, batch, 1, "student_no", None, "缺少必填列")
        failed_count += 1
    if failed_count:
        finalize_import_batch(batch, success_count, failed_count)
        db.commit()
        return _result(batch)

    student_no_column = next(position for name, position in headers if name == "student_no")
    subject_columns = [(name, position) for name, position in headers if name not in RESERVED_COLUMNS]

    for row_number, cells in _data_rows(worksheet):
        student_no = _clean(_cell(cells, student_no_column))
        exam_student = students_by_no.get(student_no)
        if not student_no or exam_student is None:
            record_import_error(
                db,
                batch,
                row_number,
                "student_no",
                _cell(cells, student_no_column),
                "考试学生不存在",
                _raw(headers, cells),
            )
            failed_count += 1
            continue
        if exam_student.status != "active":
            record_import_error(
                db,
                batch,
                row_number,
                "student_no",
                student_no,
                "考试学生或科目已停用",
                _raw(headers, cells),
            )
            failed_count += 1
            continue

        for subject_name, position in subject_columns:
            raw_value = _cell(cells, position)
            if _is_blank(raw_value):
                continue
            subject = subjects_by_name.get(subject_name)
            if subject is None:
                record_import_error(
                    db,
                    batch,
                    row_number,
                    subject_name,
                    raw_value,
                    "考试科目不存在",
                    _raw(headers, cells),
                )
                failed_count += 1
                continue
            key = (exam_student.id, subject.id)
            duplicate_in_workbook = key in seen_keys
            seen_keys.add(key)
            if subject.status != "active":
                record_import_error(
                    db,
                    batch,
                    row_number,
                    subject_name,
                    raw_value,
                    "考试学生或科目已停用",
                    _raw(headers, cells),
                )
                failed_count += 1
                continue
            if duplicate_in_workbook:
                record_import_error(
                    db,
                    batch,
                    row_number,
                    subject_name,
                    raw_value,
                    "同一文件中成绩重复",
                    _raw(headers, cells),
                )
                failed_count += 1
                continue
            if key in existing_scores and not overwrite_existing:
                record_import_error(
                    db,
                    batch,
                    row_number,
                    subject_name,
                    raw_value,
                    "成绩已存在",
                    _raw(headers, cells),
                )
                failed_count += 1
                continue
            parsed = _parse_score_value(raw_value, subject.full_score)
            if isinstance(parsed, str):
                record_import_error(db, batch, row_number, subject_name, raw_value, parsed, _raw(headers, cells))
                failed_count += 1
                continue

            score = existing_scores.get(key)
            if score is None:
                score = Score(exam_student_id=exam_student.id, exam_subject_id=subject.id)
                db.add(score)
                existing_scores[key] = score
            score.score = parsed[0]
            score.score_status = parsed[1]
            score.remark = None
            success_count += 1

    finalize_import_batch(batch, success_count, failed_count)
    return _commit_or_fail(db, batch)


def _headers(header_row) -> list[HeaderColumn]:
    return [
        (str(cell.value).strip(), index)
        for index, cell in enumerate(header_row)
        if cell.value is not None and str(cell.value).strip()
    ]


def _data_rows(worksheet):
    for index, cells in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
        if all(_is_blank(value) for value in cells):
            continue
        yield index, cells


def _parse_score_value(value: object, full_score: Decimal) -> tuple[Decimal | None, str] | str:
    text = _clean(value)
    if text in ABNORMAL_SCORE_STATUSES:
        return None, text
    try:
        score = Decimal(text)
    except (InvalidOperation, ValueError):
        return "成绩格式不支持"
    if not score.is_finite():
        return "成绩格式不支持"
    if score < Decimal("0"):
        return "分数不能小于 0"
    if score > full_score:
        return f"分数不能超过满分 {full_score:.2f}"
    return score, "normal"


def _is_blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def _cell(cells: tuple[object, ...], position: int) -> object:
    return cells[position] if position < len(cells) else None


def _raw(headers: list[HeaderColumn], cells: tuple[object, ...]) -> str:
    row = [
        {"field": field, "value": _cell(cells, position)}
        for field, position in headers
    ]
    return json.dumps(row, ensure_ascii=False, default=str)


def _result(batch) -> dict[str, object]:
    return {
        "batch_id": batch.id,
        "status": batch.status,
        "success_count": batch.success_count,
        "failed_count": batch.failed_count,
        "error_summary": batch.error_summary,
    }


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
