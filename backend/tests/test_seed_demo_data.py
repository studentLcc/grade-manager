from importlib import import_module

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models import Class, Course, Exam, ExamStudent, ExamSubject, Schedule, Score, Student


def test_demo_seed_creates_related_data_and_is_idempotent():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_module = import_module("scripts.seed_demo_data")
        config = seed_module.SeedConfig(
            username="seed-test",
            password="strong-password",
            display_name="Seed Test",
            class_count=2,
            students_per_class=3,
            course_names=("Chinese", "Math", "English"),
            subject_count=2,
            exam_count=2,
            schedule_weekdays=(1, 2),
            schedule_periods=(1, 2),
        )

        first = seed_module.seed_demo_data(db, config)
        second = seed_module.seed_demo_data(db, config)

        assert first == second
        assert first["classes"] == 2
        assert first["students"] == 6
        assert first["courses"] == 3
        assert first["schedules"] == 8
        assert first["exams"] == 2
        assert first["exam_subjects"] == 4
        assert first["exam_students"] == 12
        assert first["scores"] == 24

        assert db.scalar(select(func.count()).select_from(Class)) == 2
        assert db.scalar(select(func.count()).select_from(Student)) == 6
        assert db.scalar(select(func.count()).select_from(Course)) == 3
        assert db.scalar(select(func.count()).select_from(Schedule)) == 8
        assert db.scalar(select(func.count()).select_from(Exam)) == 2
        assert db.scalar(select(func.count()).select_from(ExamSubject)) == 4
        assert db.scalar(select(func.count()).select_from(ExamStudent)) == 12
        assert db.scalar(select(func.count()).select_from(Score)) == 24
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
