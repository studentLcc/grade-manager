from io import BytesIO

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Class, Course, ExamClass, ExamStudent, ExamSubject, Student, Teacher
from app.modules.exams.service import get_active_exam_for_mutation


def build_score_template(db: Session, teacher: Teacher, exam_id: int, class_id: int | None) -> bytes:
    exam = get_active_exam_for_mutation(db, teacher, exam_id)

    if class_id is not None:
        exam_class = db.scalar(
            select(ExamClass).where(
                ExamClass.exam_id == exam.id,
                ExamClass.class_id == class_id,
                ExamClass.status == "active",
            )
        )
        if exam_class is None:
            raise AppError(404, "NOT_FOUND", "考试班级不存在")

    subjects = db.execute(
        select(ExamSubject, Course)
        .join(Course, Course.id == ExamSubject.course_id)
        .where(ExamSubject.exam_id == exam.id, ExamSubject.status == "active")
        .order_by(ExamSubject.id)
    ).all()
    student_query = (
        select(ExamStudent, Student, Class)
        .join(Student, Student.id == ExamStudent.student_id)
        .join(Class, Class.id == ExamStudent.class_id)
        .where(ExamStudent.exam_id == exam.id, ExamStudent.status == "active")
        .order_by(ExamStudent.class_id, ExamStudent.id)
    )
    if class_id is not None:
        student_query = student_query.where(ExamStudent.class_id == class_id)
    students = db.execute(student_query).all()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "scores"
    sheet.append(["student_no", "student_name", "class_name", *[course.course_name for _, course in subjects]])
    for _, student, class_ in students:
        sheet.append([student.student_no, student.name, class_.name, *["" for _ in subjects]])

    output = BytesIO()
    workbook.save(output)
    return output.getvalue()
