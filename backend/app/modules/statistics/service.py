from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_FLOOR, ROUND_HALF_UP

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Class, Course, Exam, ExamStudent, ExamSubject, Score, Student, Teacher

ABNORMAL_STATUSES = ("absent", "deferred", "cheating", "exempt")
VALID_INCLUDED_STATUSES = {"normal", *ABNORMAL_STATUSES, "missing"}
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class ScoreEntry:
    exam_student: ExamStudent
    student: Student
    class_: Class
    subject: ExamSubject
    course: Course
    score: Score | None

    @property
    def status(self) -> str:
        return self.score.score_status if self.score is not None else "missing"

    @property
    def value(self) -> Decimal | None:
        if self.status == "normal" and self.score is not None:
            return self.score.score
        if self.status in ABNORMAL_STATUSES or self.status == "missing":
            return ZERO
        return None


def parse_included_statuses(raw: str | None) -> list[str]:
    if raw is None or raw.strip() == "":
        return ["normal"]
    statuses = [part.strip() for part in raw.split(",") if part.strip()]
    if not statuses or any(status not in VALID_INCLUDED_STATUSES for status in statuses):
        raise AppError(422, "VALIDATION_ERROR", "included_statuses 参数不支持")
    return list(dict.fromkeys(statuses))


def get_exam_summary(
    db: Session,
    teacher: Teacher,
    exam_id: int,
    included_statuses_raw: str | None,
) -> dict[str, object]:
    exam = _get_exam(db, teacher, exam_id)
    included_statuses = parse_included_statuses(included_statuses_raw)
    entries = _load_entries(db, exam.id)
    student_totals = _student_totals(entries, included_statuses)

    return {
        "exam": _exam_ref(exam),
        "included_statuses": included_statuses,
        "overall": _total_metric(student_totals),
        "class_comparison": _class_comparison(student_totals),
        "subject_comparison": _subject_comparison(entries, included_statuses),
        "abnormal_counts": {status: sum(1 for entry in entries if entry.status == status) for status in ABNORMAL_STATUSES},
        "missing_score_count": sum(1 for entry in entries if entry.status == "missing"),
        "abnormal_lists": {
            status: [_student_item(entry) for entry in entries if entry.status == status]
            for status in ABNORMAL_STATUSES
        },
        "missing_score_list": [_student_item(entry) for entry in entries if entry.status == "missing"],
    }


def get_rankings(
    db: Session,
    teacher: Teacher,
    exam_id: int,
    rank_type: str,
    exam_subject_id: int | None,
    class_id: int | None,
    included_statuses_raw: str | None,
) -> dict[str, object]:
    exam = _get_exam(db, teacher, exam_id)
    included_statuses = parse_included_statuses(included_statuses_raw)
    entries = _load_entries(db, exam.id)
    if class_id is not None:
        _ensure_class_owned(db, teacher, class_id)
        entries = [entry for entry in entries if entry.exam_student.class_id == class_id]
    if rank_type == "subject":
        if exam_subject_id is None:
            raise AppError(422, "VALIDATION_ERROR", "科目排名必须指定 exam_subject_id")
        entries = [entry for entry in entries if entry.subject.id == exam_subject_id]
        scores = [
            (entry, entry.value or ZERO)
            for entry in entries
            if entry.status in included_statuses
        ]
    elif rank_type == "total":
        scores = [
            (_first_entry(student_entries), total)
            for student_entries, total in _student_totals(entries, included_statuses)
        ]
    else:
        raise AppError(422, "VALIDATION_ERROR", "rank_type 参数不支持")

    ranked = sorted(scores, key=lambda item: (-item[1], item[0].exam_student.id))
    return {
        "exam": _exam_ref(exam),
        "included_statuses": included_statuses,
        "rank_type": rank_type,
        "exam_subject_id": exam_subject_id,
        "class_id": class_id,
        "items": [
            {
                "rank": index + 1,
                "exam_student_id": entry.exam_student.id,
                "student_id": entry.student.id,
                "student_no": entry.student.student_no,
                "name": entry.student.name,
                "class_id": entry.exam_student.class_id,
                "class_name": entry.class_.name,
                "score": _money(score),
            }
            for index, (entry, score) in enumerate(ranked)
        ],
    }


def get_segments(
    db: Session,
    teacher: Teacher,
    exam_id: int,
    segment_type: str,
    step: int,
    exam_subject_id: int | None,
    class_id: int | None,
    included_statuses_raw: str | None,
) -> dict[str, object]:
    exam = _get_exam(db, teacher, exam_id)
    included_statuses = parse_included_statuses(included_statuses_raw)
    entries = _load_entries(db, exam.id)
    if class_id is not None:
        _ensure_class_owned(db, teacher, class_id)
        entries = [entry for entry in entries if entry.exam_student.class_id == class_id]
    if segment_type == "subject":
        if exam_subject_id is None:
            raise AppError(422, "VALIDATION_ERROR", "科目分段必须指定 exam_subject_id")
        scores = [
            entry.value or ZERO
            for entry in entries
            if entry.subject.id == exam_subject_id and entry.status in included_statuses
        ]
    elif segment_type == "total":
        scores = [total for _, total in _student_totals(entries, included_statuses)]
    else:
        raise AppError(422, "VALIDATION_ERROR", "type 参数不支持")
    return {
        "exam": _exam_ref(exam),
        "included_statuses": included_statuses,
        "type": segment_type,
        "exam_subject_id": exam_subject_id,
        "step": step,
        "items": _segments(scores, step),
    }


def get_student_history(db: Session, teacher: Teacher, student_id: int) -> dict[str, object]:
    student = db.scalar(select(Student).where(Student.id == student_id, Student.teacher_id == teacher.id))
    if student is None:
        raise AppError(404, "NOT_FOUND", "学生不存在")
    rows = db.execute(
        select(ExamStudent, Exam, Class)
        .join(Exam, Exam.id == ExamStudent.exam_id)
        .join(Class, Class.id == ExamStudent.class_id)
        .where(Exam.teacher_id == teacher.id, ExamStudent.student_id == student_id, ExamStudent.status == "active")
        .order_by(Exam.created_at.desc(), Exam.id.desc())
    ).all()
    items = []
    for exam_student, exam, class_ in rows:
        entries = [
            entry
            for entry in _load_entries(db, exam.id)
            if entry.exam_student.id == exam_student.id
        ]
        totals = _student_totals(entries, ["normal"])
        total = totals[0][1] if totals else ZERO
        divisor = len([entry for entry in entries if entry.status == "normal"]) or 1
        items.append(
            {
                "exam_id": exam.id,
                "exam_name": exam.name,
                "class_id": exam_student.class_id,
                "class_name": class_.name,
                "total_score": _money(total),
                "average_score": _money(total / divisor),
            }
        )
    return {"student_id": student_id, "items": items}


def get_class_overview(db: Session, teacher: Teacher, class_id: int) -> dict[str, object]:
    _ensure_class_owned(db, teacher, class_id)
    exams = db.scalars(
        select(Exam)
        .join(ExamStudent, ExamStudent.exam_id == Exam.id)
        .where(Exam.teacher_id == teacher.id, ExamStudent.class_id == class_id, ExamStudent.status == "active")
        .distinct()
        .order_by(Exam.created_at.desc(), Exam.id.desc())
    ).all()
    items = []
    for exam in exams:
        entries = [
            entry
            for entry in _load_entries(db, exam.id)
            if entry.exam_student.class_id == class_id
        ]
        values = [entry.value or ZERO for entry in entries if entry.status == "normal"]
        if not values:
            continue
        class_name = entries[0].class_.name if entries else None
        items.append(
            {
                "exam_id": exam.id,
                "exam_name": exam.name,
                "class_id": class_id,
                "class_name": class_name,
                "average_score": _money(sum(values, ZERO) / len(values)),
            }
        )
    return {"class_id": class_id, "items": items}


def _get_exam(db: Session, teacher: Teacher, exam_id: int) -> Exam:
    exam = db.scalar(select(Exam).where(Exam.id == exam_id, Exam.teacher_id == teacher.id))
    if exam is None:
        raise AppError(404, "NOT_FOUND", "考试不存在")
    return exam


def _ensure_class_owned(db: Session, teacher: Teacher, class_id: int) -> None:
    exists = db.scalar(select(Class.id).where(Class.id == class_id, Class.teacher_id == teacher.id))
    if exists is None:
        raise AppError(404, "NOT_FOUND", "班级不存在")


def _load_entries(db: Session, exam_id: int) -> list[ScoreEntry]:
    students = db.execute(
        select(ExamStudent, Student, Class)
        .join(Student, Student.id == ExamStudent.student_id)
        .join(Class, Class.id == ExamStudent.class_id)
        .where(ExamStudent.exam_id == exam_id, ExamStudent.status == "active")
        .order_by(ExamStudent.id)
    ).all()
    subjects = db.execute(
        select(ExamSubject, Course)
        .join(Course, Course.id == ExamSubject.course_id)
        .where(ExamSubject.exam_id == exam_id, ExamSubject.status == "active")
        .order_by(ExamSubject.id)
    ).all()
    scores = {
        (score.exam_student_id, score.exam_subject_id): score
        for score in db.scalars(
            select(Score)
            .join(ExamStudent, ExamStudent.id == Score.exam_student_id)
            .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
            .where(
                ExamStudent.exam_id == exam_id,
                ExamSubject.exam_id == exam_id,
                ExamStudent.status == "active",
                ExamSubject.status == "active",
            )
        )
    }
    return [
        ScoreEntry(
            exam_student=exam_student,
            student=student,
            class_=class_,
            subject=subject,
            course=course,
            score=scores.get((exam_student.id, subject.id)),
        )
        for exam_student, student, class_ in students
        for subject, course in subjects
    ]


def _included_entries(entries: list[ScoreEntry], included_statuses: list[str]) -> list[ScoreEntry]:
    return [entry for entry in entries if entry.status in included_statuses]


def _student_totals(
    entries: list[ScoreEntry],
    included_statuses: list[str],
) -> list[tuple[list[ScoreEntry], Decimal]]:
    grouped: dict[int, list[ScoreEntry]] = defaultdict(list)
    for entry in entries:
        grouped[entry.exam_student.id].append(entry)
    totals = []
    for student_entries in grouped.values():
        included = _included_entries(student_entries, included_statuses)
        if included:
            totals.append((included, sum((entry.value or ZERO for entry in included), ZERO)))
    return totals


def _metric(values: list[Decimal], pass_score: Decimal, excellent_score: Decimal) -> dict[str, Decimal]:
    if not values:
        return {
            "average_score": ZERO,
            "highest_score": ZERO,
            "lowest_score": ZERO,
            "pass_rate": ZERO,
            "excellent_rate": ZERO,
        }
    return {
        "average_score": _money(sum(values, ZERO) / len(values)),
        "highest_score": _money(max(values)),
        "lowest_score": _money(min(values)),
        "pass_rate": _percent(sum(1 for value in values if value >= pass_score), len(values)),
        "excellent_rate": _percent(sum(1 for value in values if value >= excellent_score), len(values)),
    }


def _total_metric(student_totals: list[tuple[list[ScoreEntry], Decimal]]) -> dict[str, Decimal]:
    if not student_totals:
        return {
            "average_score": ZERO,
            "highest_score": ZERO,
            "lowest_score": ZERO,
            "pass_rate": ZERO,
            "excellent_rate": ZERO,
        }
    totals = [total for _, total in student_totals]
    pass_count = sum(
        1
        for student_entries, total in student_totals
        if total >= _total_pass_score(student_entries)
    )
    excellent_count = sum(
        1
        for student_entries, total in student_totals
        if total >= _total_excellent_score(student_entries)
    )
    return {
        "average_score": _money(sum(totals, ZERO) / len(totals)),
        "highest_score": _money(max(totals)),
        "lowest_score": _money(min(totals)),
        "pass_rate": _percent(pass_count, len(student_totals)),
        "excellent_rate": _percent(excellent_count, len(student_totals)),
    }


def _class_comparison(
    student_totals: list[tuple[list[ScoreEntry], Decimal]],
) -> list[dict[str, object]]:
    by_class: dict[int, list[tuple[list[ScoreEntry], Decimal]]] = defaultdict(list)
    names: dict[int, str] = {}
    for student_entries, total in student_totals:
        first = _first_entry(student_entries)
        by_class[first.exam_student.class_id].append((student_entries, total))
        names[first.exam_student.class_id] = first.class_.name
    return [
        {"id": class_id, "name": names[class_id], **_total_metric(class_totals)}
        for class_id, class_totals in sorted(by_class.items())
    ]


def _subject_comparison(
    entries: list[ScoreEntry],
    included_statuses: list[str],
) -> list[dict[str, object]]:
    by_subject: dict[int, list[ScoreEntry]] = defaultdict(list)
    for entry in entries:
        if entry.status in included_statuses:
            by_subject[entry.subject.id].append(entry)
    result = []
    for subject_id, subject_entries in sorted(by_subject.items()):
        subject = subject_entries[0].subject
        result.append(
            {
                "id": subject_id,
                "name": subject_entries[0].course.course_name,
                **_metric(
                    [entry.value or ZERO for entry in subject_entries],
                    subject.pass_score or ZERO,
                    subject.excellent_score or subject.full_score,
                ),
            }
        )
    return result


def _total_pass_score(entries: list[ScoreEntry]) -> Decimal:
    subjects = {entry.subject.id: entry.subject for entry in entries}
    return sum((subject.pass_score or ZERO for subject in subjects.values()), ZERO)


def _total_excellent_score(entries: list[ScoreEntry]) -> Decimal:
    subjects = {entry.subject.id: entry.subject for entry in entries}
    return sum((subject.excellent_score or subject.full_score for subject in subjects.values()), ZERO)


def _segments(values: list[Decimal], step: int) -> list[dict[str, object]]:
    if step <= 0:
        raise AppError(422, "VALIDATION_ERROR", "step 必须大于 0")
    if not values:
        return []
    max_score = max(values)
    top = int((max_score / step).to_integral_value(rounding=ROUND_FLOOR)) * step
    if max_score % step != 0:
        top += step
    top = max(top, step)
    buckets = [{"label": f"[{start}, {start + step})", "start": Decimal(start), "end": Decimal(start + step), "count": 0} for start in range(0, top, step)]
    buckets[-1]["label"] = f"[{top - step}, {top}]"
    for value in values:
        index = min(int(value // step), len(buckets) - 1)
        buckets[index]["count"] += 1
    return buckets


def _student_item(entry: ScoreEntry) -> dict[str, object]:
    return {
        "exam_student_id": entry.exam_student.id,
        "student_id": entry.student.id,
        "student_no": entry.student.student_no,
        "name": entry.student.name,
        "class_id": entry.exam_student.class_id,
        "class_name": entry.class_.name,
        "exam_subject_id": entry.subject.id,
        "course_name": entry.course.course_name,
    }


def _first_entry(entries: list[ScoreEntry]) -> ScoreEntry:
    return sorted(entries, key=lambda entry: entry.subject.id)[0]


def _exam_ref(exam: Exam) -> dict[str, object]:
    return {"id": exam.id, "name": exam.name}


def _money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _percent(count: int, total: int) -> Decimal:
    if total == 0:
        return ZERO
    return _money(Decimal(count) * Decimal("100") / Decimal(total))
