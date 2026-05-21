from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.course import Course
    from app.models.exam import Exam
    from app.models.import_ import ImportBatch
    from app.models.schedule import Schedule
    from app.models.student import Student


class Teacher(TimestampMixin, Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
    )

    classes: Mapped[list["Class"]] = relationship("Class", back_populates="teacher")
    students: Mapped[list["Student"]] = relationship("Student", back_populates="teacher")
    courses: Mapped[list["Course"]] = relationship("Course", back_populates="teacher")
    schedules: Mapped[list["Schedule"]] = relationship("Schedule", back_populates="teacher")
    exams: Mapped[list["Exam"]] = relationship("Exam", back_populates="teacher")
    import_batches: Mapped[list["ImportBatch"]] = relationship(
        "ImportBatch",
        back_populates="teacher",
    )
