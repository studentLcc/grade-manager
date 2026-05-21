from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.exam import ExamClass, ExamStudent
    from app.models.schedule import Schedule
    from app.models.student import Student
    from app.models.teacher import Teacher


class Class(TimestampMixin, Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(50), nullable=True)
    academic_year: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="classes")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="class_")
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="class_")
    exam_classes: Mapped[list["ExamClass"]] = relationship("ExamClass", back_populates="class_")
    exam_students: Mapped[list["ExamStudent"]] = relationship(
        "ExamStudent",
        back_populates="class_",
    )
