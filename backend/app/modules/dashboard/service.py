from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import app_now
from app.models import Class, Course, Exam, ExamStudent, ExamSubject, Schedule, Score, Student, Teacher
from app.modules.statistics.service import ABNORMAL_STATUSES, ZERO


def get_dashboard_summary(db: Session, teacher: Teacher) -> dict[str, object]:
    return {
        "class_count": _count(db, select(func.count()).select_from(Class).where(Class.teacher_id == teacher.id, Class.status == "active")),
        "student_count": _count(db, select(func.count()).select_from(Student).where(Student.teacher_id == teacher.id, Student.status == "active")),
        "course_count": _count(db, select(func.count()).select_from(Course).where(Course.teacher_id == teacher.id, Course.status == "active")),
        "recent_exam_count": _count(db, select(func.count()).select_from(Exam).where(Exam.teacher_id == teacher.id, Exam.status == "active")),
        "pending_score_count": _pending_score_count(db, teacher),
    }


def get_today_schedule(db: Session, teacher: Teacher) -> dict[str, object]:
    weekday = app_now().isoweekday()
    rows = db.execute(
        select(Schedule, Class, Course)
        .join(Class, Class.id == Schedule.class_id)
        .join(Course, Course.id == Schedule.course_id)
        .where(Schedule.teacher_id == teacher.id, Schedule.status == "active", Schedule.weekday == weekday)
        .order_by(Schedule.period_no, Schedule.id)
    ).all()
    return {
        "items": [
            {
                "id": schedule.id,
                "class_id": schedule.class_id,
                "class_name": class_.name,
                "course_id": schedule.course_id,
                "course_name": course.course_name,
                "weekday": schedule.weekday,
                "period_no": schedule.period_no,
                "start_time": schedule.start_time,
                "end_time": schedule.end_time,
                "location": schedule.location,
            }
            for schedule, class_, course in rows
        ]
    }


def get_recent_exams(db: Session, teacher: Teacher) -> dict[str, object]:
    latest_subject_date = func.max(ExamSubject.exam_date)
    rows = db.execute(
        select(Exam, latest_subject_date.label("latest_subject_date"))
        .outerjoin(
            ExamSubject,
            (ExamSubject.exam_id == Exam.id) & (ExamSubject.status == "active"),
        )
        .where(Exam.teacher_id == teacher.id, Exam.status == "active")
        .group_by(Exam.id)
        .order_by(latest_subject_date.is_(None).asc(), latest_subject_date.desc(), Exam.created_at.desc(), Exam.id.desc())
        .limit(10)
    ).all()
    return {
        "items": [
            {"id": exam.id, "name": exam.name, "exam_type": exam.exam_type, "term": exam.term}
            for exam, _ in rows
        ]
    }


def get_score_overview(
    db: Session,
    teacher: Teacher,
    class_id: int | None = None,
    academic_year: str | None = None,
) -> dict[str, object]:
    if class_id is not None:
        _ensure_class_owned(db, teacher, class_id)
    exam = _latest_exam_for_scope(db, teacher, class_id=class_id, academic_year=academic_year)
    if exam is None:
        return _empty_score_overview()
    filters = [
        ExamStudent.exam_id == exam.id,
        ExamSubject.exam_id == exam.id,
        Class.teacher_id == teacher.id,
        ExamStudent.status == "active",
        ExamSubject.status == "active",
    ]
    if class_id is not None:
        filters.append(ExamStudent.class_id == class_id)
    if academic_year:
        filters.append(Class.academic_year == academic_year)
    rows = db.execute(
        select(Score, ExamSubject)
        .join(ExamStudent, ExamStudent.id == Score.exam_student_id)
        .join(Class, Class.id == ExamStudent.class_id)
        .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
        .where(*filters)
    ).all()
    normal_values = [score.score for score, _ in rows if score.score_status == "normal" and score.score is not None]
    normal_count = len(normal_values)
    abnormal_distribution = {
        status: sum(1 for score, _ in rows if score.score_status == status)
        for status in ABNORMAL_STATUSES
    }
    failing_count = sum(
        1
        for score, subject in rows
        if score.score_status == "normal"
        and score.score is not None
        and subject.pass_score is not None
        and score.score < subject.pass_score
    )
    low_score_warning = sum(
        1
        for score, subject in rows
        if score.score_status == "normal"
        and score.score is not None
        and subject.pass_score is not None
        and score.score < subject.pass_score + Decimal("10")
    )
    return {
        "latest_exam": {"id": exam.id, "name": exam.name},
        "average_score": _money(sum(normal_values, ZERO) / len(normal_values)) if normal_values else ZERO,
        "highest_score": _money(max(normal_values)) if normal_values else ZERO,
        "lowest_score": _money(min(normal_values)) if normal_values else ZERO,
        "abnormal_count": sum(abnormal_distribution.values()),
        "abnormal_distribution": abnormal_distribution,
        "normal_count": normal_count,
        "reference_count": normal_count + sum(abnormal_distribution.values()),
        "low_score_warning": low_score_warning,
        "failing_count": failing_count,
        "absent_count": abnormal_distribution["absent"],
        "cheating_count": abnormal_distribution["cheating"],
    }


def get_class_average_trend(db: Session, teacher: Teacher, academic_year: str | None = None) -> dict[str, object]:
    filters = [
        Exam.teacher_id == teacher.id,
        Exam.status == "active",
        Class.teacher_id == teacher.id,
        ExamStudent.status == "active",
        ExamSubject.status == "active",
        Score.score_status == "normal",
        Score.score.is_not(None),
    ]
    if academic_year:
        filters.append(Class.academic_year == academic_year)
    rows = db.execute(
        select(Exam, ExamStudent, Class, Score)
        .join(ExamStudent, ExamStudent.exam_id == Exam.id)
        .join(Class, Class.id == ExamStudent.class_id)
        .join(Score, Score.exam_student_id == ExamStudent.id)
        .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
        .where(*filters)
        .order_by(Exam.created_at.desc(), Exam.id.desc())
    ).all()
    grouped: dict[tuple[int, int], list[Decimal]] = {}
    names: dict[tuple[int, int], tuple[str, str]] = {}
    for exam, exam_student, class_, score in rows:
        key = (exam.id, exam_student.class_id)
        grouped.setdefault(key, []).append(score.score)
        names[key] = (exam.name, class_.name)
    return {
        "items": [
            {
                "exam_id": exam_id,
                "exam_name": names[(exam_id, class_id)][0],
                "class_id": class_id,
                "class_name": names[(exam_id, class_id)][1],
                "average_score": _money(sum(values, ZERO) / len(values)),
            }
            for (exam_id, class_id), values in grouped.items()
        ]
    }


def _pending_score_count(db: Session, teacher: Teacher) -> int:
    rows = db.execute(
        select(Exam.id, ExamStudent.id, ExamSubject.id)
        .join(ExamStudent, ExamStudent.exam_id == Exam.id)
        .join(ExamSubject, ExamSubject.exam_id == Exam.id)
        .where(
            Exam.teacher_id == teacher.id,
            Exam.status == "active",
            ExamStudent.status == "active",
            ExamSubject.status == "active",
        )
    ).all()
    existing = {
        (exam_student_id, exam_subject_id)
        for exam_student_id, exam_subject_id in db.execute(
            select(Score.exam_student_id, Score.exam_subject_id)
            .join(ExamStudent, ExamStudent.id == Score.exam_student_id)
            .join(Exam, Exam.id == ExamStudent.exam_id)
            .where(Exam.teacher_id == teacher.id)
        ).all()
    }
    return sum(1 for _, exam_student_id, exam_subject_id in rows if (exam_student_id, exam_subject_id) not in existing)


def _empty_score_overview() -> dict[str, object]:
    return {
        "latest_exam": None,
        "average_score": ZERO,
        "highest_score": ZERO,
        "lowest_score": ZERO,
        "abnormal_count": 0,
        "abnormal_distribution": {status: 0 for status in ABNORMAL_STATUSES},
        "normal_count": 0,
        "reference_count": 0,
        "low_score_warning": 0,
        "failing_count": 0,
        "absent_count": 0,
        "cheating_count": 0,
    }


def _count(db: Session, query) -> int:
    return int(db.scalar(query) or 0)


def _latest_exam_for_scope(
    db: Session,
    teacher: Teacher,
    class_id: int | None = None,
    academic_year: str | None = None,
) -> Exam | None:
    filters = [
        Exam.teacher_id == teacher.id,
        Exam.status == "active",
    ]
    if class_id is not None or academic_year:
        filters.extend(
            [
                Class.teacher_id == teacher.id,
                ExamStudent.status == "active",
            ]
        )
        if class_id is not None:
            filters.append(ExamStudent.class_id == class_id)
        if academic_year:
            filters.append(Class.academic_year == academic_year)
        return db.scalar(
            select(Exam)
            .join(ExamStudent, ExamStudent.exam_id == Exam.id)
            .join(Class, Class.id == ExamStudent.class_id)
            .where(*filters)
            .order_by(Exam.created_at.desc(), Exam.id.desc())
            .limit(1)
        )
    return db.scalar(
        select(Exam)
        .where(*filters)
        .order_by(Exam.created_at.desc(), Exam.id.desc())
        .limit(1)
    )


def _ensure_class_owned(db: Session, teacher: Teacher, class_id: int) -> None:
    exists = db.scalar(select(Class.id).where(Class.id == class_id, Class.teacher_id == teacher.id))
    if exists is None:
        raise AppError(404, "NOT_FOUND", "班级不存在")


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
