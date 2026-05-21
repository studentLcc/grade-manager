from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.exam import ExamStudent, ExamSubject


class Score(TimestampMixin, Base):
    __tablename__ = "scores"
    __table_args__ = (
        UniqueConstraint(
            "exam_student_id",
            "exam_subject_id",
            name="uq_scores_exam_student_subject",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_student_id: Mapped[int] = mapped_column(
        ForeignKey("exam_students.id"),
        nullable=False,
        index=True,
    )
    exam_subject_id: Mapped[int] = mapped_column(
        ForeignKey("exam_subjects.id"),
        nullable=False,
        index=True,
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    score_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="normal",
        server_default="normal",
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)

    exam_student: Mapped["ExamStudent"] = relationship("ExamStudent", back_populates="scores")
    exam_subject: Mapped["ExamSubject"] = relationship("ExamSubject", back_populates="scores")
