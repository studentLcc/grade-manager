from sqlalchemy import delete, exists, select
from sqlalchemy.orm import Session

from app.models import Exam, ExamClass, ExamStudent, ExamSubject, Score, Student


def has_exam_scores(db: Session, exam_id: int) -> bool:
    return db.scalar(
        select(exists().where(Score.exam_subject_id == ExamSubject.id, ExamSubject.exam_id == exam_id))
    )


def ensure_exam_roster(db: Session, exam: Exam) -> None:
    class_ids = list(
        db.scalars(
            select(ExamClass.class_id).where(
                ExamClass.exam_id == exam.id,
                ExamClass.status == "active",
            )
        )
    )
    active_students = list(
        db.scalars(
            select(Student).where(
                Student.class_id.in_(class_ids),
                Student.status == "active",
            )
        )
    ) if class_ids else []

    if not has_exam_scores(db, exam.id):
        db.execute(delete(ExamStudent).where(ExamStudent.exam_id == exam.id))
        for student in active_students:
            if student.class_id is not None:
                db.add(
                    ExamStudent(
                        exam_id=exam.id,
                        student_id=student.id,
                        class_id=student.class_id,
                        status="active",
                    )
                )
        db.flush()
        return

    existing_by_student_id = {
        row.student_id: row
        for row in db.scalars(select(ExamStudent).where(ExamStudent.exam_id == exam.id))
    }
    for student in active_students:
        existing = existing_by_student_id.get(student.id)
        if existing is not None:
            if existing.class_id in class_ids:
                existing.status = "active"
        elif student.class_id is not None:
            db.add(
                ExamStudent(
                    exam_id=exam.id,
                    student_id=student.id,
                    class_id=student.class_id,
                    status="active",
                )
            )
    db.flush()
