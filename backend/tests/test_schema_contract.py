from decimal import Decimal

from sqlalchemy import create_engine, inspect

from app.core.database import Base
from app.models import (
    Class,
    Course,
    Exam,
    ExamClass,
    ExamStudent,
    ExamSubject,
    ImportBatch,
    ImportError,
    Schedule,
    Score,
    Student,
    Teacher,
)


def test_all_expected_tables_are_registered():
    assert all(
        model is not None
        for model in (
            Class,
            Course,
            Exam,
            ExamClass,
            ExamStudent,
            ExamSubject,
            ImportBatch,
            ImportError,
            Schedule,
            Score,
            Student,
            Teacher,
        )
    )
    assert {
        "teachers",
        "classes",
        "students",
        "courses",
        "schedules",
        "exams",
        "exam_classes",
        "exam_subjects",
        "exam_students",
        "scores",
        "import_batches",
        "import_errors",
    } <= set(Base.metadata.tables)


def test_score_column_uses_decimal_scale():
    score_column = Score.__table__.c.score
    assert score_column.type.scale == 2
    assert score_column.type.precision == 6
    assert Decimal("99.50") == Decimal("99.50")


def test_unique_constraints_exist():
    constraints = {
        constraint.name
        for table in Base.metadata.tables.values()
        for constraint in table.constraints
        if constraint.name
    }
    assert "uq_students_teacher_student_no" in constraints
    assert "uq_courses_teacher_course_name" in constraints
    assert "uq_schedules_active_slot" in constraints
    assert "uq_exam_classes_exam_class" in constraints
    assert "uq_exam_subjects_exam_course" in constraints
    assert "uq_exam_students_exam_student" in constraints
    assert "uq_scores_exam_student_subject" in constraints


def test_relationships_are_mapped_annotations():
    expected_relationships = {
        Teacher: {
            "classes",
            "students",
            "courses",
            "schedules",
            "exams",
            "import_batches",
        },
        Class: {"teacher", "students", "schedules", "exam_classes", "exam_students"},
        Course: {"teacher", "schedules", "exam_subjects"},
        Student: {"teacher", "class_", "exam_students"},
        Schedule: {"teacher", "class_", "course"},
        Exam: {"teacher", "exam_classes", "exam_subjects", "exam_students"},
        ExamClass: {"exam", "class_"},
        ExamSubject: {"exam", "course", "scores"},
        ExamStudent: {"exam", "student", "class_", "scores"},
        Score: {"exam_student", "exam_subject"},
        ImportBatch: {
            "teacher",
            "target_class",
            "target_exam",
            "target_exam_subject",
            "errors",
        },
        ImportError: {"batch"},
    }

    for model, relationship_names in expected_relationships.items():
        annotations = model.__dict__.get("__annotations__", {})
        for relationship_name in relationship_names:
            assert relationship_name in annotations, (
                f"{model.__name__}.{relationship_name} must be annotated with Mapped[...]"
            )


def test_python_defaults_have_matching_server_defaults():
    expected_defaults = {
        Teacher: {"status": "active"},
        Class: {"status": "active"},
        Course: {"status": "active"},
        Student: {"status": "active"},
        Schedule: {"status": "active"},
        Exam: {"status": "active"},
        ExamClass: {"status": "active"},
        ExamSubject: {"status": "active"},
        ExamStudent: {"status": "active"},
        Score: {"score_status": "normal"},
        ImportBatch: {
            "status": "pending",
            "success_count": "0",
            "failed_count": "0",
        },
    }

    for model, column_defaults in expected_defaults.items():
        for column_name, expected_default in column_defaults.items():
            default = model.__table__.c[column_name].server_default
            assert default is not None, f"{model.__name__}.{column_name} is missing server_default"
            assert str(default.arg) == expected_default


def test_models_can_create_sqlite_schema():
    local_engine = create_engine("sqlite+pysqlite:///:memory:")
    try:
        Base.metadata.create_all(bind=local_engine)
        table_names = inspect(local_engine).get_table_names()
        assert "teachers" in table_names
        assert "scores" in table_names
    finally:
        local_engine.dispose()
