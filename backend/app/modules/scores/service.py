from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Class, Course, Exam, ExamClass, ExamStudent, ExamSubject, Score, Student, Teacher
from app.modules.exams.service import get_active_exam_for_mutation, get_exam
from app.modules.exams.roster_service import ensure_exam_roster
from app.modules.scores.schemas import ScoreFailureItem, ScoreSaveItem, ScoreSaveRequest

ABNORMAL_SCORE_STATUSES = {"absent", "deferred", "cheating", "exempt"}


def list_score_records(
    db: Session,
    teacher: Teacher,
    page: int,
    page_size: int,
    keyword: str | None = None,
    exam_id: int | None = None,
    class_id: int | None = None,
    course_id: int | None = None,
    status: str | None = None,
    score_status: str | None = None,
) -> tuple[list[dict[str, object]], int]:
    score_status_expr = func.coalesce(Score.score_status, "normal")
    query = (
        select(ExamStudent, ExamSubject, Class, Student, Course, Score)
        .join(Exam, Exam.id == ExamStudent.exam_id)
        .join(ExamSubject, ExamSubject.exam_id == ExamStudent.exam_id)
        .join(Class, Class.id == ExamStudent.class_id)
        .join(Student, Student.id == ExamStudent.student_id)
        .join(Course, Course.id == ExamSubject.course_id)
        .outerjoin(
            Score,
            (Score.exam_student_id == ExamStudent.id)
            & (Score.exam_subject_id == ExamSubject.id),
        )
        .where(
            Exam.teacher_id == teacher.id,
            ExamStudent.status == "active",
            ExamSubject.status == "active",
        )
        .order_by(
            Exam.created_at.desc(),
            Exam.id.desc(),
            Class.name,
            Student.student_no,
            ExamSubject.id,
        )
    )
    if status is None:
        query = query.where(Exam.status == "active")
    else:
        query = query.where(Exam.status == status)
    if keyword:
        query = query.where(
            or_(
                Exam.name.contains(keyword),
                Student.student_no.contains(keyword),
                Student.name.contains(keyword),
                Course.course_name.contains(keyword),
            )
        )
    if exam_id:
        query = query.where(Exam.id == exam_id)
    if class_id:
        query = query.where(ExamStudent.class_id == class_id)
    if course_id:
        query = query.where(ExamSubject.course_id == course_id)
    if score_status:
        query = query.where(score_status_expr == score_status)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.offset((page - 1) * page_size).limit(page_size)).all()
    return [_serialize_score_record(*row) for row in rows], total


def get_score_sheet(db: Session, teacher: Teacher, exam_id: int) -> dict[str, object]:
    exam = get_exam(db, teacher, exam_id)
    if exam.status == "active":
        ensure_exam_roster(db, exam)
        db.commit()

    classes = db.execute(
        select(ExamClass, Class)
        .join(Class, Class.id == ExamClass.class_id)
        .where(ExamClass.exam_id == exam.id, ExamClass.status == "active")
        .order_by(ExamClass.id)
    ).all()
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
    scores = db.scalars(
        select(Score)
        .join(ExamStudent, ExamStudent.id == Score.exam_student_id)
        .join(ExamSubject, ExamSubject.id == Score.exam_subject_id)
        .where(
            ExamStudent.exam_id == exam.id,
            ExamSubject.exam_id == exam.id,
            ExamStudent.status == "active",
            ExamSubject.status == "active",
        )
        .order_by(Score.exam_student_id, Score.exam_subject_id)
    ).all()

    return {
        "exam": {
            "id": exam.id,
            "name": exam.name,
            "exam_type": exam.exam_type,
            "term": exam.term,
            "status": exam.status,
        },
        "classes": [{"id": class_.id, "name": class_.name} for _, class_ in classes],
        "subjects": [
            {
                "exam_subject_id": subject.id,
                "course_id": subject.course_id,
                "course_name": course.course_name,
                "full_score": subject.full_score,
                "pass_score": subject.pass_score,
                "excellent_score": subject.excellent_score,
                "status": subject.status,
            }
            for subject, course in subjects
        ],
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
        "scores": [
            {
                "exam_student_id": score.exam_student_id,
                "exam_subject_id": score.exam_subject_id,
                "score": score.score,
                "score_status": score.score_status,
                "remark": score.remark or "",
            }
            for score in scores
        ],
    }


def _serialize_score_record(
    exam_student: ExamStudent,
    exam_subject: ExamSubject,
    class_: Class,
    student: Student,
    course: Course,
    score: Score | None,
) -> dict[str, object]:
    exam = exam_student.exam
    return {
        "exam_id": exam.id,
        "exam_name": exam.name,
        "term": exam.term,
        "exam_status": exam.status,
        "class_id": class_.id,
        "class_name": class_.name,
        "student_id": student.id,
        "student_no": student.student_no,
        "student_name": student.name,
        "exam_student_id": exam_student.id,
        "course_id": course.id,
        "course_name": course.course_name,
        "exam_subject_id": exam_subject.id,
        "full_score": exam_subject.full_score,
        "score": score.score if score is not None else None,
        "score_status": score.score_status if score is not None else "normal",
        "remark": score.remark if score is not None and score.remark is not None else "",
    }


def save_scores(db: Session, teacher: Teacher, exam_id: int, payload: ScoreSaveRequest) -> dict[str, object]:
    exam = get_active_exam_for_mutation(db, teacher, exam_id)
    students = {
        row.id: row
        for row in db.scalars(select(ExamStudent).where(ExamStudent.exam_id == exam.id)).all()
    }
    subjects = {
        row.id: row
        for row in db.scalars(select(ExamSubject).where(ExamSubject.exam_id == exam.id)).all()
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

    success_count = 0
    failed_items: list[ScoreFailureItem] = []
    pending_scores: dict[tuple[int, int], Score] = {}

    for index, item in enumerate(payload.items):
        reason = _validate_score_item(item, students, subjects)
        if reason is not None:
            failed_items.append(
                ScoreFailureItem(
                    index=index,
                    exam_student_id=item.exam_student_id,
                    exam_subject_id=item.exam_subject_id,
                    reason=reason,
                )
            )
            continue

        key = (item.exam_student_id, item.exam_subject_id)
        score = pending_scores.get(key) or existing_scores.get(key)
        if score is None:
            score = Score(exam_student_id=item.exam_student_id, exam_subject_id=item.exam_subject_id)
            db.add(score)
        score.score = item.score
        score.score_status = item.score_status
        score.remark = item.remark
        pending_scores[key] = score
        success_count += 1

    db.commit()
    return {
        "success_count": success_count,
        "failure_count": len(failed_items),
        "failed_items": [item.model_dump(exclude_none=True) for item in failed_items],
    }


def _validate_score_item(
    item: ScoreSaveItem,
    students: dict[int, ExamStudent],
    subjects: dict[int, ExamSubject],
) -> str | None:
    if "student_id" in item.model_extra or "class_id" in item.model_extra:
        return "成绩保存不能直接指定学生或班级"

    exam_student = students.get(item.exam_student_id)
    if exam_student is None:
        return "考试学生不存在"
    exam_subject = subjects.get(item.exam_subject_id)
    if exam_subject is None:
        return "考试科目不存在"
    if exam_student.status != "active" or exam_subject.status != "active":
        return "考试学生或科目已停用"

    if item.score_status == "normal":
        if item.score is None:
            return "正常状态必须填写数字成绩"
        if item.score < Decimal("0"):
            return "分数不能小于 0"
        if item.score > exam_subject.full_score:
            return f"分数不能超过满分 {exam_subject.full_score:.2f}"
        return None

    if item.score_status in ABNORMAL_SCORE_STATUSES:
        if item.score is not None:
            return "异常状态不能填写数字成绩"
        return None

    return "成绩状态不支持"
