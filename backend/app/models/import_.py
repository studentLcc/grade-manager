from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.class_ import Class
    from app.models.exam import Exam, ExamSubject
    from app.models.teacher import Teacher


class ImportBatch(TimestampMixin, Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"), nullable=False, index=True)
    import_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id"), nullable=True)
    target_exam_id: Mapped[int | None] = mapped_column(ForeignKey("exams.id"), nullable=True)
    target_exam_subject_id: Mapped[int | None] = mapped_column(
        ForeignKey("exam_subjects.id"),
        nullable=True,
    )
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        server_default="pending",
    )
    success_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(nullable=False, default=0, server_default="0")
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="import_batches")
    target_class: Mapped["Class | None"] = relationship("Class")
    target_exam: Mapped["Exam | None"] = relationship("Exam")
    target_exam_subject: Mapped["ExamSubject | None"] = relationship("ExamSubject")
    errors: Mapped[list["ImportError"]] = relationship("ImportError", back_populates="batch")


class ImportError(Base):
    __tablename__ = "import_errors"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False, index=True)
    row_number: Mapped[int | None] = mapped_column(nullable=True)
    field: Mapped[str | None] = mapped_column(String(100), nullable=True)
    raw_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    batch: Mapped["ImportBatch"] = relationship("ImportBatch", back_populates="errors")
