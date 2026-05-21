from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.models import Class, Course, Exam, ExamClass, ExamStudent, ExamSubject, Score, Student, Teacher
from app.modules.exams.roster_service import ensure_exam_roster, has_exam_scores
from app.modules.exams.schemas import (
    ExamClassesUpdate,
    ExamCreate,
    ExamSubjectsUpdate,
    ExamUpdate,
    ScoreSaveRequest,
)


def get_exam(db: Session, teacher: Teacher, exam_id: int) -> Exam:
    exam = db.scalar(
        select(Exam)
        .options(
            selectinload(Exam.exam_classes).selectinload(ExamClass.class_),
            selectinload(Exam.exam_subjects).selectinload(ExamSubject.course),
        )
        .where(Exam.id == exam_id, Exam.teacher_id == teacher.id)
    )
    if exam is None:
        raise AppError(404, "NOT_FOUND", "考试不存在")
    return exam


def create_exam(db: Session, teacher: Teacher, payload: ExamCreate) -> Exam:
    _ensure_classes_owned(db, teacher, payload.class_ids)
    _ensure_courses_owned(db, teacher, [subject.course_id for subject in payload.subjects])
    _ensure_unique_course_ids([subject.course_id for subject in payload.subjects])

    exam = Exam(
        teacher_id=teacher.id,
        name=payload.name,
        exam_type=payload.exam_type,
        term=payload.term,
        remark=payload.remark,
    )
    db.add(exam)
    db.flush()
    for class_id in dict.fromkeys(payload.class_ids):
        db.add(ExamClass(exam_id=exam.id, class_id=class_id, status="active"))
    for subject in payload.subjects:
        db.add(ExamSubject(exam_id=exam.id, **subject.model_dump(), status="active"))
    db.flush()
    ensure_exam_roster(db, exam)
    db.commit()
    return get_exam(db, teacher, exam.id)


def update_exam(db: Session, teacher: Teacher, exam_id: int, payload: ExamUpdate) -> Exam:
    exam = get_exam(db, teacher, exam_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(exam, field, value)
    db.commit()
    return get_exam(db, teacher, exam_id)


def update_exam_classes(
    db: Session,
    teacher: Teacher,
    exam_id: int,
    payload: ExamClassesUpdate,
) -> Exam:
    exam = get_exam(db, teacher, exam_id)
    requested_ids = list(dict.fromkeys(payload.class_ids))
    _ensure_classes_owned(db, teacher, requested_ids)
    scored = has_exam_scores(db, exam.id)

    current_rows = {
        row.class_id: row
        for row in db.scalars(select(ExamClass).where(ExamClass.exam_id == exam.id))
    }
    current_active_ids = {class_id for class_id, row in current_rows.items() if row.status == "active"}
    requested_set = set(requested_ids)

    if not scored:
        for row in current_rows.values():
            row.status = "inactive"
        for class_id in requested_ids:
            if class_id in current_rows:
                current_rows[class_id].status = "active"
            else:
                db.add(ExamClass(exam_id=exam.id, class_id=class_id, status="active"))
        db.flush()
        ensure_exam_roster(db, exam)
        db.commit()
        return get_exam(db, teacher, exam.id)

    removing = current_active_ids - requested_set
    for class_id in removing:
        if _class_has_scores(db, exam.id, class_id):
            raise AppError(422, "VALIDATION_ERROR", "已有成绩的班级不能从考试中移除")

    for class_id in requested_ids:
        if class_id in current_rows:
            current_rows[class_id].status = "active"
        else:
            db.add(ExamClass(exam_id=exam.id, class_id=class_id, status="active"))
    for class_id in removing:
        current_rows[class_id].status = "inactive"
        for exam_student in db.scalars(
            select(ExamStudent).where(
                ExamStudent.exam_id == exam.id,
                ExamStudent.class_id == class_id,
            )
        ):
            exam_student.status = "inactive"
    db.flush()
    ensure_exam_roster(db, exam)
    db.commit()
    return get_exam(db, teacher, exam.id)


def update_exam_subjects(
    db: Session,
    teacher: Teacher,
    exam_id: int,
    payload: ExamSubjectsUpdate,
) -> Exam:
    exam = get_exam(db, teacher, exam_id)
    course_ids = [subject.course_id for subject in payload.subjects]
    _ensure_unique_course_ids(course_ids)
    _ensure_courses_owned(db, teacher, course_ids)

    existing = {
        subject.id: subject
        for subject in db.scalars(select(ExamSubject).where(ExamSubject.exam_id == exam.id))
    }
    requested_ids = {subject.id for subject in payload.subjects if subject.id is not None}
    for subject_id in requested_ids:
        if subject_id not in existing:
            raise AppError(404, "NOT_FOUND", "考试科目不存在")

    for subject_id, subject in existing.items():
        if subject_id not in requested_ids and _subject_has_scores(db, subject_id):
            raise AppError(422, "VALIDATION_ERROR", "已有成绩的考试科目不能从考试中移除")
        if subject_id not in requested_ids:
            db.delete(subject)

    for item in payload.subjects:
        if item.id is None:
            db.add(
                ExamSubject(
                    exam_id=exam.id,
                    **item.model_dump(exclude={"id", "status"}),
                    status=item.status or "active",
                )
            )
            continue

        subject = existing[item.id]
        if _subject_has_scores(db, subject.id) and item.course_id != subject.course_id:
            raise AppError(422, "VALIDATION_ERROR", "已有成绩的考试科目不能更换课程")
        _reject_full_score_below_existing_score(db, subject.id, item.full_score)
        subject.course_id = item.course_id
        subject.full_score = item.full_score
        subject.pass_score = item.pass_score
        subject.excellent_score = item.excellent_score
        subject.exam_date = item.exam_date
        subject.remark = item.remark
        if item.status is not None:
            subject.status = item.status

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "DUPLICATE_RESOURCE", "考试科目重复") from exc
    return get_exam(db, teacher, exam.id)


def get_score_sheet(db: Session, teacher: Teacher, exam_id: int) -> dict[str, object]:
    exam = get_exam(db, teacher, exam_id)
    ensure_exam_roster(db, exam)
    db.commit()

    students = db.execute(
        select(ExamStudent, Student)
        .join(Student, Student.id == ExamStudent.student_id)
        .where(ExamStudent.exam_id == exam.id, ExamStudent.status == "active")
        .order_by(ExamStudent.id)
    ).all()
    subjects = db.execute(
        select(ExamSubject, Course)
        .join(Course, Course.id == ExamSubject.course_id)
        .where(ExamSubject.exam_id == exam.id, ExamSubject.status == "active")
        .order_by(ExamSubject.id)
    ).all()
    return {
        "exam_id": exam.id,
        "students": [
            {
                "exam_student_id": exam_student.id,
                "student_id": student.id,
                "class_id": exam_student.class_id,
                "student_no": student.student_no,
                "name": student.name,
                "status": exam_student.status,
            }
            for exam_student, student in students
        ],
        "subjects": [
            {
                "exam_subject_id": subject.id,
                "course_id": subject.course_id,
                "course_name": course.course_name,
                "full_score": subject.full_score,
                "pass_score": subject.pass_score,
                "excellent_score": subject.excellent_score,
                "exam_date": subject.exam_date,
                "status": subject.status,
            }
            for subject, course in subjects
        ],
    }


def save_scores(db: Session, teacher: Teacher, exam_id: int, payload: ScoreSaveRequest) -> dict[str, int]:
    exam = get_exam(db, teacher, exam_id)
    count = 0
    for item in payload.items:
        exam_student = db.scalar(
            select(ExamStudent).where(
                ExamStudent.id == item.exam_student_id,
                ExamStudent.exam_id == exam.id,
            )
        )
        exam_subject = db.scalar(
            select(ExamSubject).where(
                ExamSubject.id == item.exam_subject_id,
                ExamSubject.exam_id == exam.id,
            )
        )
        if exam_student is None or exam_subject is None:
            raise AppError(404, "NOT_FOUND", "考试学生或科目不存在")
        if exam_student.status != "active" or exam_subject.status != "active":
            raise AppError(422, "VALIDATION_ERROR", "考试学生或科目已停用")
        score = db.scalar(
            select(Score).where(
                Score.exam_student_id == item.exam_student_id,
                Score.exam_subject_id == item.exam_subject_id,
            )
        )
        if score is None:
            score = Score(
                exam_student_id=item.exam_student_id,
                exam_subject_id=item.exam_subject_id,
            )
            db.add(score)
        score.score = item.score
        score.score_status = item.score_status
        score.remark = item.remark
        count += 1
    db.commit()
    return {"saved": count}


def serialize_exam(exam: Exam) -> dict[str, object]:
    return {
        "id": exam.id,
        "name": exam.name,
        "exam_type": exam.exam_type,
        "term": exam.term,
        "status": exam.status,
        "remark": exam.remark,
        "classes": [
            {"id": row.class_.id, "name": row.class_.name}
            for row in exam.exam_classes
            if row.status == "active"
        ],
        "subjects": [
            {
                "id": subject.id,
                "course_id": subject.course_id,
                "course_name": subject.course.course_name if subject.course is not None else None,
                "full_score": subject.full_score,
                "pass_score": subject.pass_score,
                "excellent_score": subject.excellent_score,
                "exam_date": subject.exam_date,
                "status": subject.status,
                "remark": subject.remark,
            }
            for subject in exam.exam_subjects
            if subject.status == "active"
        ],
    }


def _ensure_classes_owned(db: Session, teacher: Teacher, class_ids: list[int]) -> None:
    found = set(
        db.scalars(
            select(Class.id).where(
                Class.id.in_(class_ids),
                Class.teacher_id == teacher.id,
            )
        )
    ) if class_ids else set()
    if found != set(class_ids):
        raise AppError(404, "NOT_FOUND", "班级不存在")


def _ensure_courses_owned(db: Session, teacher: Teacher, course_ids: list[int]) -> None:
    found = set(
        db.scalars(
            select(Course.id).where(
                Course.id.in_(course_ids),
                Course.teacher_id == teacher.id,
            )
        )
    ) if course_ids else set()
    if found != set(course_ids):
        raise AppError(404, "NOT_FOUND", "课程不存在")


def _ensure_unique_course_ids(course_ids: list[int]) -> None:
    if len(set(course_ids)) != len(course_ids):
        raise AppError(422, "VALIDATION_ERROR", "考试科目不能重复")


def _class_has_scores(db: Session, exam_id: int, class_id: int) -> bool:
    return bool(
        db.scalar(
            select(Score.id)
            .join(ExamStudent, ExamStudent.id == Score.exam_student_id)
            .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
            .where(
                ExamStudent.exam_id == exam_id,
                ExamSubject.exam_id == exam_id,
                ExamStudent.class_id == class_id,
            )
            .limit(1)
        )
    )


def _subject_has_scores(db: Session, exam_subject_id: int) -> bool:
    return bool(db.scalar(select(Score.id).where(Score.exam_subject_id == exam_subject_id).limit(1)))


def _reject_full_score_below_existing_score(
    db: Session,
    exam_subject_id: int,
    full_score: Decimal,
) -> None:
    highest = db.scalar(
        select(func.max(Score.score)).where(
            Score.exam_subject_id == exam_subject_id,
            Score.score_status == "normal",
            Score.score.is_not(None),
        )
    )
    if highest is not None and full_score < highest:
        raise AppError(422, "VALIDATION_ERROR", "满分不能低于已有最高成绩")
