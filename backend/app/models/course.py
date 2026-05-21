from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.exam import ExamSubject
    from app.models.schedule import Schedule
    from app.models.teacher import Teacher


class Course(TimestampMixin, Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("teacher_id", "course_name", name="uq_courses_teacher_course_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    course_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="courses")
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="course")
    exam_subjects: Mapped[list["ExamSubject"]] = relationship(
        "ExamSubject",
        back_populates="course",
    )
