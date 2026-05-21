"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-21 00:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_teachers_username"), "teachers", ["username"], unique=False)

    op.create_table(
        "classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("grade", sa.String(length=50), nullable=True),
        sa.Column("academic_year", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_classes_teacher_id"), "classes", ["teacher_id"], unique=False)

    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("course_name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("teacher_id", "course_name", name="uq_courses_teacher_course_name"),
    )
    op.create_index(op.f("ix_courses_teacher_id"), "courses", ["teacher_id"], unique=False)

    op.create_table(
        "exams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("exam_type", sa.String(length=50), nullable=True),
        sa.Column("term", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_exams_teacher_id"), "exams", ["teacher_id"], unique=False)

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=True),
        sa.Column("student_no", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("teacher_id", "student_no", name="uq_students_teacher_student_no"),
    )
    op.create_index(op.f("ix_students_class_id"), "students", ["class_id"], unique=False)
    op.create_index(op.f("ix_students_teacher_id"), "students", ["teacher_id"], unique=False)

    op.create_table(
        "schedules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("period_no", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "teacher_id",
            "class_id",
            "weekday",
            "period_no",
            name="uq_schedules_active_slot",
        ),
    )
    op.create_index(op.f("ix_schedules_class_id"), "schedules", ["class_id"], unique=False)
    op.create_index(op.f("ix_schedules_course_id"), "schedules", ["course_id"], unique=False)
    op.create_index(op.f("ix_schedules_teacher_id"), "schedules", ["teacher_id"], unique=False)

    op.create_table(
        "exam_classes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "class_id", name="uq_exam_classes_exam_class"),
    )
    op.create_index(op.f("ix_exam_classes_class_id"), "exam_classes", ["class_id"], unique=False)
    op.create_index(op.f("ix_exam_classes_exam_id"), "exam_classes", ["exam_id"], unique=False)

    op.create_table(
        "exam_subjects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("full_score", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("pass_score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("excellent_score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("exam_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"]),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "course_id", name="uq_exam_subjects_exam_course"),
    )
    op.create_index(op.f("ix_exam_subjects_course_id"), "exam_subjects", ["course_id"], unique=False)
    op.create_index(op.f("ix_exam_subjects_exam_id"), "exam_subjects", ["exam_id"], unique=False)

    op.create_table(
        "exam_students",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("class_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="active", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "student_id", name="uq_exam_students_exam_student"),
    )
    op.create_index(op.f("ix_exam_students_class_id"), "exam_students", ["class_id"], unique=False)
    op.create_index(op.f("ix_exam_students_exam_id"), "exam_students", ["exam_id"], unique=False)
    op.create_index(op.f("ix_exam_students_student_id"), "exam_students", ["student_id"], unique=False)

    op.create_table(
        "import_batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("import_type", sa.String(length=20), nullable=False),
        sa.Column("target_class_id", sa.Integer(), nullable=True),
        sa.Column("target_exam_id", sa.Integer(), nullable=True),
        sa.Column("target_exam_subject_id", sa.Integer(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("success_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("failed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["target_class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["target_exam_id"], ["exams.id"]),
        sa.ForeignKeyConstraint(["target_exam_subject_id"], ["exam_subjects.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_batches_teacher_id"), "import_batches", ["teacher_id"], unique=False)

    op.create_table(
        "scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exam_student_id", sa.Integer(), nullable=False),
        sa.Column("exam_subject_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("score_status", sa.String(length=20), server_default="normal", nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["exam_student_id"], ["exam_students.id"]),
        sa.ForeignKeyConstraint(["exam_subject_id"], ["exam_subjects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_student_id", "exam_subject_id", name="uq_scores_exam_student_subject"),
    )
    op.create_index(op.f("ix_scores_exam_student_id"), "scores", ["exam_student_id"], unique=False)
    op.create_index(op.f("ix_scores_exam_subject_id"), "scores", ["exam_subject_id"], unique=False)

    op.create_table(
        "import_errors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=True),
        sa.Column("field", sa.String(length=100), nullable=True),
        sa.Column("raw_value", sa.Text(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("raw_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_import_errors_batch_id"), "import_errors", ["batch_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_import_errors_batch_id"), table_name="import_errors")
    op.drop_table("import_errors")
    op.drop_index(op.f("ix_scores_exam_subject_id"), table_name="scores")
    op.drop_index(op.f("ix_scores_exam_student_id"), table_name="scores")
    op.drop_table("scores")
    op.drop_index(op.f("ix_import_batches_teacher_id"), table_name="import_batches")
    op.drop_table("import_batches")
    op.drop_index(op.f("ix_exam_students_student_id"), table_name="exam_students")
    op.drop_index(op.f("ix_exam_students_exam_id"), table_name="exam_students")
    op.drop_index(op.f("ix_exam_students_class_id"), table_name="exam_students")
    op.drop_table("exam_students")
    op.drop_index(op.f("ix_exam_subjects_exam_id"), table_name="exam_subjects")
    op.drop_index(op.f("ix_exam_subjects_course_id"), table_name="exam_subjects")
    op.drop_table("exam_subjects")
    op.drop_index(op.f("ix_exam_classes_exam_id"), table_name="exam_classes")
    op.drop_index(op.f("ix_exam_classes_class_id"), table_name="exam_classes")
    op.drop_table("exam_classes")
    op.drop_index(op.f("ix_schedules_teacher_id"), table_name="schedules")
    op.drop_index(op.f("ix_schedules_course_id"), table_name="schedules")
    op.drop_index(op.f("ix_schedules_class_id"), table_name="schedules")
    op.drop_table("schedules")
    op.drop_index(op.f("ix_students_teacher_id"), table_name="students")
    op.drop_index(op.f("ix_students_class_id"), table_name="students")
    op.drop_table("students")
    op.drop_index(op.f("ix_exams_teacher_id"), table_name="exams")
    op.drop_table("exams")
    op.drop_index(op.f("ix_courses_teacher_id"), table_name="courses")
    op.drop_table("courses")
    op.drop_index(op.f("ix_classes_teacher_id"), table_name="classes")
    op.drop_table("classes")
    op.drop_index(op.f("ix_teachers_username"), table_name="teachers")
    op.drop_table("teachers")
