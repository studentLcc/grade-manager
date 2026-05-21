from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.course import Course
    from app.models.score import Score
    from app.models.student import Student
    from app.models.teacher import Teacher


class Exam(TimestampMixin, Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    term: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="exams")
    exam_classes: Mapped[list["ExamClass"]] = relationship("ExamClass", back_populates="exam")
    exam_subjects: Mapped[list["ExamSubject"]] = relationship(
        "ExamSubject",
        back_populates="exam",
    )
    exam_students: Mapped[list["ExamStudent"]] = relationship(
        "ExamStudent",
        back_populates="exam",
    )


class ExamClass(Base):
    __tablename__ = "exam_classes"
    __table_args__ = (
        UniqueConstraint("exam_id", "class_id", name="uq_exam_classes_exam_class"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    exam: Mapped["Exam"] = relationship("Exam", back_populates="exam_classes")
    class_: Mapped["Class"] = relationship("Class", back_populates="exam_classes")


class ExamSubject(TimestampMixin, Base):
    __tablename__ = "exam_subjects"
    __table_args__ = (
        UniqueConstraint("exam_id", "course_id", name="uq_exam_subjects_exam_course"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False, index=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    full_score: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    pass_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    excellent_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam: Mapped["Exam"] = relationship("Exam", back_populates="exam_subjects")
    course: Mapped["Course"] = relationship("Course", back_populates="exam_subjects")
    scores: Mapped[list["Score"]] = relationship("Score", back_populates="exam_subject")


class ExamStudent(Base):
    __tablename__ = "exam_students"
    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_exam_students_exam_student"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.id"), nullable=False, index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    exam: Mapped["Exam"] = relationship("Exam", back_populates="exam_students")
    student: Mapped["Student"] = relationship("Student", back_populates="exam_students")
    class_: Mapped["Class"] = relationship("Class", back_populates="exam_students")
    scores: Mapped[list["Score"]] = relationship("Score", back_populates="exam_student")
