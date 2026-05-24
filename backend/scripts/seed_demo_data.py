from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, time, timedelta
from decimal import Decimal
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    Class,
    Course,
    Exam,
    ExamClass,
    ExamStudent,
    ExamSubject,
    Schedule,
    Score,
    Student,
    Teacher,
)


@dataclass(frozen=True)
class SeedConfig:
    username: str = "teacher1"
    password: str = "strong-password"
    display_name: str = "王老师"
    class_count: int = 8
    students_per_class: int = 40
    course_names: Sequence[str] = (
        "语文",
        "数学",
        "英语",
        "物理",
        "化学",
        "生物",
        "历史",
        "地理",
        "政治",
        "体育",
    )
    subject_count: int = 6
    exam_count: int = 6
    schedule_weekdays: Sequence[int] = (1, 2, 3, 4, 5)
    schedule_periods: Sequence[int] = (1, 2, 3, 4, 5, 6)


GENDERS = ("男", "女")
GRADES = ("七年级", "八年级", "九年级")
EXAM_NAMES = (
    "开学摸底",
    "第一次月考",
    "期中考试",
    "第二次月考",
    "期末考试",
    "综合诊断",
    "寒假返校测验",
    "学业水平模拟",
)
SURNAMES = (
    "赵",
    "钱",
    "孙",
    "李",
    "周",
    "吴",
    "郑",
    "王",
    "冯",
    "陈",
    "刘",
    "杨",
    "黄",
    "林",
    "何",
    "高",
)
GIVEN_NAMES = (
    "一鸣",
    "子涵",
    "雨欣",
    "浩然",
    "思远",
    "梓萱",
    "嘉琪",
    "明轩",
    "若曦",
    "宇航",
    "晨曦",
    "欣怡",
    "博文",
    "雅婷",
    "俊杰",
    "诗涵",
)


def seed_demo_data(db: Session, config: SeedConfig | None = None) -> dict[str, int]:
    config = config or SeedConfig()
    teacher = _ensure_teacher(db, config)
    courses = _ensure_courses(db, teacher, config)
    classes = _ensure_classes(db, teacher, config)
    students = _ensure_students(db, teacher, classes, config)
    schedules = _ensure_schedules(db, teacher, classes, courses, config)
    exams = _ensure_exams(db, teacher, classes, courses, students, config)

    db.commit()
    return _seed_counts(db, teacher, classes, students, courses, schedules, exams, config)


def _ensure_teacher(db: Session, config: SeedConfig) -> Teacher:
    teacher = db.scalar(select(Teacher).where(Teacher.username == config.username))
    if teacher is not None:
        teacher.display_name = teacher.display_name or config.display_name
        teacher.status = "active"
        db.flush()
        return teacher

    teacher = Teacher(
        username=config.username,
        password_hash=hash_password(config.password),
        display_name=config.display_name,
        email=f"{config.username}@example.com",
        phone="13800000000",
        status="active",
    )
    db.add(teacher)
    db.flush()
    return teacher


def _ensure_courses(db: Session, teacher: Teacher, config: SeedConfig) -> list[Course]:
    courses: list[Course] = []
    existing = {
        course.course_name: course
        for course in db.scalars(select(Course).where(Course.teacher_id == teacher.id))
    }
    for index, name in enumerate(config.course_names, start=1):
        course = existing.get(name)
        if course is None:
            course = Course(
                teacher_id=teacher.id,
                course_name=name,
                remark=f"演示课程 {index:02d}",
                status="active",
            )
            db.add(course)
            db.flush()
        else:
            course.status = "active"
            course.remark = course.remark or f"演示课程 {index:02d}"
        courses.append(course)
    db.flush()
    return courses


def _ensure_classes(db: Session, teacher: Teacher, config: SeedConfig) -> list[Class]:
    classes: list[Class] = []
    existing = {
        class_.name: class_
        for class_ in db.scalars(select(Class).where(Class.teacher_id == teacher.id))
    }
    for index in range(1, config.class_count + 1):
        name = _class_name(index)
        class_ = existing.get(name)
        if class_ is None:
            class_ = Class(
                teacher_id=teacher.id,
                name=name,
                grade=GRADES[(index - 1) % len(GRADES)],
                academic_year="2026-2027",
                status="active",
                remark=f"演示班级 {index:02d}",
            )
            db.add(class_)
            db.flush()
        else:
            class_.grade = class_.grade or GRADES[(index - 1) % len(GRADES)]
            class_.academic_year = class_.academic_year or "2026-2027"
            class_.status = "active"
        classes.append(class_)
    db.flush()
    return classes


def _ensure_students(
    db: Session,
    teacher: Teacher,
    classes: Sequence[Class],
    config: SeedConfig,
) -> list[Student]:
    existing = {
        student.student_no: student
        for student in db.scalars(select(Student).where(Student.teacher_id == teacher.id))
    }
    students: list[Student] = []
    for class_index, class_ in enumerate(classes, start=1):
        for student_index in range(1, config.students_per_class + 1):
            student_no = _student_no(class_index, student_index)
            student = existing.get(student_no)
            if student is None:
                student = Student(
                    teacher_id=teacher.id,
                    class_id=class_.id,
                    student_no=student_no,
                    name=_student_name(class_index, student_index),
                    gender=GENDERS[(class_index + student_index) % len(GENDERS)],
                    remark="演示学生",
                    status="active",
                )
                db.add(student)
                db.flush()
            else:
                student.class_id = class_.id
                student.status = "active"
                student.gender = student.gender or GENDERS[(class_index + student_index) % len(GENDERS)]
                student.remark = student.remark or "演示学生"
            students.append(student)
    db.flush()
    return students


def _ensure_schedules(
    db: Session,
    teacher: Teacher,
    classes: Sequence[Class],
    courses: Sequence[Course],
    config: SeedConfig,
) -> list[Schedule]:
    existing = {
        (schedule.class_id, schedule.weekday, schedule.period_no): schedule
        for schedule in db.scalars(select(Schedule).where(Schedule.teacher_id == teacher.id))
    }
    schedules: list[Schedule] = []
    for class_index, class_ in enumerate(classes, start=1):
        for weekday in config.schedule_weekdays:
            for period in config.schedule_periods:
                course = courses[(class_index + weekday + period - 3) % len(courses)]
                start_time, end_time = _period_time(period)
                key = (class_.id, weekday, period)
                schedule = existing.get(key)
                if schedule is None:
                    schedule = Schedule(
                        teacher_id=teacher.id,
                        class_id=class_.id,
                        course_id=course.id,
                        weekday=weekday,
                        period_no=period,
                        start_time=start_time,
                        end_time=end_time,
                        location=f"教学楼 {class_index:02d}-{period:02d}",
                        remark="演示课表",
                        status="active",
                    )
                    db.add(schedule)
                    db.flush()
                else:
                    schedule.course_id = course.id
                    schedule.start_time = start_time
                    schedule.end_time = end_time
                    schedule.location = schedule.location or f"教学楼 {class_index:02d}-{period:02d}"
                    schedule.status = "active"
                schedules.append(schedule)
    db.flush()
    return schedules


def _ensure_exams(
    db: Session,
    teacher: Teacher,
    classes: Sequence[Class],
    courses: Sequence[Course],
    students: Sequence[Student],
    config: SeedConfig,
) -> list[Exam]:
    subject_courses = list(courses[: config.subject_count])
    existing = {
        (exam.name, exam.term): exam
        for exam in db.scalars(select(Exam).where(Exam.teacher_id == teacher.id))
    }
    exams: list[Exam] = []
    for exam_index in range(1, config.exam_count + 1):
        name = _exam_name(exam_index)
        term = "2026-2027-1" if exam_index <= max(config.exam_count // 2, 1) else "2026-2027-2"
        exam = existing.get((name, term))
        if exam is None:
            exam = Exam(
                teacher_id=teacher.id,
                name=name,
                exam_type="school",
                term=term,
                remark="演示考试",
                status="active",
            )
            db.add(exam)
            db.flush()
        else:
            exam.status = "active"
            exam.exam_type = exam.exam_type or "school"
            exam.remark = exam.remark or "演示考试"

        _ensure_exam_classes(db, exam, classes)
        subjects = _ensure_exam_subjects(db, exam, subject_courses, exam_index)
        exam_students = _ensure_exam_students(db, exam, students)
        _ensure_scores(db, exam_students, subjects, exam_index)
        exams.append(exam)
    db.flush()
    return exams


def _ensure_exam_classes(db: Session, exam: Exam, classes: Sequence[Class]) -> None:
    existing = {
        exam_class.class_id: exam_class
        for exam_class in db.scalars(select(ExamClass).where(ExamClass.exam_id == exam.id))
    }
    for class_ in classes:
        exam_class = existing.get(class_.id)
        if exam_class is None:
            db.add(ExamClass(exam_id=exam.id, class_id=class_.id, status="active"))
        else:
            exam_class.status = "active"
    db.flush()


def _ensure_exam_subjects(
    db: Session,
    exam: Exam,
    courses: Sequence[Course],
    exam_index: int,
) -> list[ExamSubject]:
    existing = {
        subject.course_id: subject
        for subject in db.scalars(select(ExamSubject).where(ExamSubject.exam_id == exam.id))
    }
    subjects: list[ExamSubject] = []
    base_date = date(2026, 9, 1) + timedelta(days=exam_index * 24)
    for subject_index, course in enumerate(courses, start=1):
        full_score = Decimal("120.00") if course.course_name in {"语文", "数学", "英语"} else Decimal("100.00")
        subject = existing.get(course.id)
        if subject is None:
            subject = ExamSubject(
                exam_id=exam.id,
                course_id=course.id,
                full_score=full_score,
                pass_score=(full_score * Decimal("0.60")).quantize(Decimal("0.01")),
                excellent_score=(full_score * Decimal("0.85")).quantize(Decimal("0.01")),
                exam_date=base_date + timedelta(days=subject_index - 1),
                remark="演示考试科目",
                status="active",
            )
            db.add(subject)
            db.flush()
        else:
            subject.full_score = full_score
            subject.pass_score = (full_score * Decimal("0.60")).quantize(Decimal("0.01"))
            subject.excellent_score = (full_score * Decimal("0.85")).quantize(Decimal("0.01"))
            subject.exam_date = subject.exam_date or base_date + timedelta(days=subject_index - 1)
            subject.status = "active"
        subjects.append(subject)
    db.flush()
    return subjects


def _ensure_exam_students(
    db: Session,
    exam: Exam,
    students: Sequence[Student],
) -> list[ExamStudent]:
    existing = {
        exam_student.student_id: exam_student
        for exam_student in db.scalars(select(ExamStudent).where(ExamStudent.exam_id == exam.id))
    }
    exam_students: list[ExamStudent] = []
    for student in students:
        if student.class_id is None:
            continue
        exam_student = existing.get(student.id)
        if exam_student is None:
            exam_student = ExamStudent(
                exam_id=exam.id,
                student_id=student.id,
                class_id=student.class_id,
                status="active",
            )
            db.add(exam_student)
            db.flush()
        else:
            exam_student.class_id = student.class_id
            exam_student.status = "active"
        exam_students.append(exam_student)
    db.flush()
    return exam_students


def _ensure_scores(
    db: Session,
    exam_students: Sequence[ExamStudent],
    subjects: Sequence[ExamSubject],
    exam_index: int,
) -> None:
    student_ids = [exam_student.id for exam_student in exam_students]
    subject_ids = [subject.id for subject in subjects]
    if not student_ids or not subject_ids:
        return

    existing = {
        (score.exam_student_id, score.exam_subject_id): score
        for score in db.scalars(
            select(Score).where(
                Score.exam_student_id.in_(student_ids),
                Score.exam_subject_id.in_(subject_ids),
            )
        )
    }
    for row_index, exam_student in enumerate(exam_students, start=1):
        for subject_index, subject in enumerate(subjects, start=1):
            key = (exam_student.id, subject.id)
            score = existing.get(key)
            score_value, score_status, remark = _score_value(
                row_index,
                subject_index,
                exam_index,
                subject.full_score,
            )
            if score is None:
                score = Score(
                    exam_student_id=exam_student.id,
                    exam_subject_id=subject.id,
                    score=score_value,
                    score_status=score_status,
                    remark=remark,
                )
                db.add(score)
            else:
                score.score = score_value
                score.score_status = score_status
                score.remark = remark
    db.flush()


def _seed_counts(
    db: Session,
    teacher: Teacher,
    classes: Sequence[Class],
    students: Sequence[Student],
    courses: Sequence[Course],
    schedules: Sequence[Schedule],
    exams: Sequence[Exam],
    config: SeedConfig,
) -> dict[str, int]:
    class_ids = [class_.id for class_ in classes]
    student_ids = [student.id for student in students]
    course_ids = [course.id for course in courses]
    schedule_ids = [schedule.id for schedule in schedules]
    exam_ids = [exam.id for exam in exams]
    subject_course_ids = course_ids[: config.subject_count]

    exam_subject_ids = list(
        db.scalars(
            select(ExamSubject.id).where(
                ExamSubject.exam_id.in_(exam_ids),
                ExamSubject.course_id.in_(subject_course_ids),
            )
        )
    )
    exam_student_ids = list(
        db.scalars(
            select(ExamStudent.id).where(
                ExamStudent.exam_id.in_(exam_ids),
                ExamStudent.student_id.in_(student_ids),
            )
        )
    )

    return {
        "teachers": db.scalar(
            select(func.count()).select_from(Teacher).where(Teacher.id == teacher.id)
        )
        or 0,
        "classes": _count_ids(db, Class, class_ids),
        "students": _count_ids(db, Student, student_ids),
        "courses": _count_ids(db, Course, course_ids),
        "schedules": _count_ids(db, Schedule, schedule_ids),
        "exams": _count_ids(db, Exam, exam_ids),
        "exam_subjects": _count_ids(db, ExamSubject, exam_subject_ids),
        "exam_students": _count_ids(db, ExamStudent, exam_student_ids),
        "scores": db.scalar(
            select(func.count())
            .select_from(Score)
            .where(
                Score.exam_student_id.in_(exam_student_ids),
                Score.exam_subject_id.in_(exam_subject_ids),
            )
        )
        or 0,
    }


def _count_ids(db: Session, model, ids: Sequence[int]) -> int:
    if not ids:
        return 0
    return db.scalar(select(func.count()).select_from(model).where(model.id.in_(ids))) or 0


def _class_name(index: int) -> str:
    return f"演示 {index:02d} 班"


def _student_no(class_index: int, student_index: int) -> str:
    return f"D2026{class_index:02d}{student_index:02d}"


def _student_name(class_index: int, student_index: int) -> str:
    surname = SURNAMES[(class_index + student_index - 2) % len(SURNAMES)]
    given_name = GIVEN_NAMES[(class_index * 3 + student_index - 4) % len(GIVEN_NAMES)]
    return f"{surname}{given_name}"


def _period_time(period: int) -> tuple[time, time]:
    starts = {
        1: time(8, 0),
        2: time(8, 55),
        3: time(10, 0),
        4: time(10, 55),
        5: time(14, 0),
        6: time(14, 55),
        7: time(16, 0),
        8: time(16, 55),
    }
    start = starts.get(period, time(8 + period, 0))
    if period in starts:
        end_hour = start.hour
        end_minute = start.minute + 45
        if end_minute >= 60:
            end_hour += 1
            end_minute -= 60
        return start, time(end_hour, end_minute)
    return start, time(min(start.hour + 1, 23), start.minute)


def _exam_name(index: int) -> str:
    suffix = EXAM_NAMES[(index - 1) % len(EXAM_NAMES)]
    return f"2026-2027 学年{suffix}"


def _score_value(
    row_index: int,
    subject_index: int,
    exam_index: int,
    full_score: Decimal,
) -> tuple[Decimal | None, str, str]:
    marker = row_index + subject_index * 7 + exam_index * 11
    if marker % 47 == 0:
        return None, "absent", "缺考"
    if marker % 53 == 0:
        return None, "deferred", "缓考"
    if marker % 59 == 0:
        return None, "exempt", "免考"

    ratio = Decimal(58 + (marker % 40)) / Decimal("100")
    score = (full_score * ratio).quantize(Decimal("0.01"))
    return min(score, full_score), "normal", "演示成绩"


def _build_config(args: argparse.Namespace) -> SeedConfig:
    return SeedConfig(
        username=args.username,
        password=args.password,
        display_name=args.display_name,
        class_count=args.classes,
        students_per_class=args.students_per_class,
        exam_count=args.exams,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the development database with demo data.")
    parser.add_argument("--username", default=SeedConfig.username)
    parser.add_argument("--password", default=SeedConfig.password)
    parser.add_argument("--display-name", default=SeedConfig.display_name)
    parser.add_argument("--classes", type=int, default=SeedConfig.class_count)
    parser.add_argument("--students-per-class", type=int, default=SeedConfig.students_per_class)
    parser.add_argument("--exams", type=int, default=SeedConfig.exam_count)
    args = parser.parse_args()

    if args.classes < 1 or args.students_per_class < 1 or args.exams < 1:
        raise SystemExit("classes, students-per-class, and exams must be greater than 0")

    db = SessionLocal()
    try:
        counts = seed_demo_data(db, _build_config(args))
        for key, value in counts.items():
            print(f"{key}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
