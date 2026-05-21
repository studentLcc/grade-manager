from datetime import time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.pagination import paginate
from app.models import Class, Course, Schedule, Teacher
from app.modules.schedules.schemas import ScheduleCreate, ScheduleUpdate


def _ensure_class_belongs_to_teacher(db: Session, teacher: Teacher, class_id: int) -> None:
    exists = db.scalar(select(Class.id).where(Class.id == class_id, Class.teacher_id == teacher.id))
    if exists is None:
        raise AppError(404, "NOT_FOUND", "班级不存在")


def _ensure_course_belongs_to_teacher(db: Session, teacher: Teacher, course_id: int) -> None:
    exists = db.scalar(
        select(Course.id).where(Course.id == course_id, Course.teacher_id == teacher.id)
    )
    if exists is None:
        raise AppError(404, "NOT_FOUND", "课程不存在")


def _validate_schedule_fields(
    weekday: int | None,
    period_no: int | None,
    start_time: time | None,
    end_time: time | None,
) -> None:
    if weekday is not None and not 1 <= weekday <= 7:
        raise AppError(422, "VALIDATION_ERROR", "星期必须在 1 到 7 之间")
    if period_no is not None and period_no <= 0:
        raise AppError(422, "VALIDATION_ERROR", "节次必须大于 0")
    if start_time is not None and end_time is not None and start_time >= end_time:
        raise AppError(422, "VALIDATION_ERROR", "开始时间必须早于结束时间")


def _ensure_unique_schedule_slot(
    db: Session,
    teacher: Teacher,
    class_id: int,
    weekday: int,
    period_no: int,
    exclude_id: int | None = None,
) -> None:
    query = select(Schedule.id).where(
        Schedule.teacher_id == teacher.id,
        Schedule.class_id == class_id,
        Schedule.weekday == weekday,
        Schedule.period_no == period_no,
        Schedule.status == "active",
    )
    if exclude_id is not None:
        query = query.where(Schedule.id != exclude_id)
    if db.scalar(query) is not None:
        raise AppError(409, "DUPLICATE_RESOURCE", "课程表时间段已存在")


def _get_inactive_schedule_slot(
    db: Session,
    teacher: Teacher,
    class_id: int,
    weekday: int,
    period_no: int,
) -> Schedule | None:
    return db.scalar(
        select(Schedule).where(
            Schedule.teacher_id == teacher.id,
            Schedule.class_id == class_id,
            Schedule.weekday == weekday,
            Schedule.period_no == period_no,
            Schedule.status != "active",
        )
    )


def list_schedules(
    db: Session,
    teacher: Teacher,
    page: int,
    page_size: int,
    keyword: str | None = None,
    status: str | None = None,
    class_id: int | None = None,
) -> tuple[list[Schedule], int]:
    query = (
        select(Schedule)
        .join(Schedule.class_)
        .join(Schedule.course)
        .where(Schedule.teacher_id == teacher.id)
    )
    if keyword:
        query = query.where(
            Class.name.like(f"%{keyword}%")
            | Course.course_name.like(f"%{keyword}%")
            | Schedule.location.like(f"%{keyword}%")
        )
    query = query.where(Schedule.status == (status or "active"))
    if class_id is not None:
        query = query.where(Schedule.class_id == class_id)
    query = query.order_by(Schedule.id.desc())
    return paginate(db, query, page, page_size)


def get_schedule(db: Session, teacher: Teacher, schedule_id: int) -> Schedule:
    schedule = db.scalar(
        select(Schedule).where(Schedule.id == schedule_id, Schedule.teacher_id == teacher.id)
    )
    if schedule is None:
        raise AppError(404, "NOT_FOUND", "课程表不存在")
    return schedule


def create_schedule(db: Session, teacher: Teacher, payload: ScheduleCreate) -> Schedule:
    _ensure_class_belongs_to_teacher(db, teacher, payload.class_id)
    _ensure_course_belongs_to_teacher(db, teacher, payload.course_id)
    _validate_schedule_fields(
        payload.weekday,
        payload.period_no,
        payload.start_time,
        payload.end_time,
    )
    _ensure_unique_schedule_slot(db, teacher, payload.class_id, payload.weekday, payload.period_no)
    inactive_schedule = _get_inactive_schedule_slot(
        db,
        teacher,
        payload.class_id,
        payload.weekday,
        payload.period_no,
    )
    if inactive_schedule is not None:
        for field, value in payload.model_dump().items():
            setattr(inactive_schedule, field, value)
        inactive_schedule.status = "active"
        db.commit()
        db.refresh(inactive_schedule)
        return inactive_schedule
    schedule = Schedule(teacher_id=teacher.id, **payload.model_dump())
    db.add(schedule)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "DUPLICATE_RESOURCE", "课程表时间段已存在") from exc
    db.refresh(schedule)
    return schedule


def update_schedule(
    db: Session,
    teacher: Teacher,
    schedule_id: int,
    payload: ScheduleUpdate,
) -> Schedule:
    schedule = get_schedule(db, teacher, schedule_id)
    data = payload.model_dump(exclude_unset=True)
    class_id = data.get("class_id", schedule.class_id)
    course_id = data.get("course_id", schedule.course_id)
    weekday = data.get("weekday", schedule.weekday)
    period_no = data.get("period_no", schedule.period_no)
    start_time = data.get("start_time", schedule.start_time)
    end_time = data.get("end_time", schedule.end_time)

    if "class_id" in data:
        _ensure_class_belongs_to_teacher(db, teacher, class_id)
    if "course_id" in data:
        _ensure_course_belongs_to_teacher(db, teacher, course_id)
    _validate_schedule_fields(weekday, period_no, start_time, end_time)
    if any(field in data for field in ("class_id", "weekday", "period_no")):
        _ensure_unique_schedule_slot(
            db,
            teacher,
            class_id,
            weekday,
            period_no,
            exclude_id=schedule_id,
        )

    for field, value in data.items():
        setattr(schedule, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(409, "DUPLICATE_RESOURCE", "课程表时间段已存在") from exc
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, teacher: Teacher, schedule_id: int) -> Schedule:
    schedule = get_schedule(db, teacher, schedule_id)
    schedule.status = "inactive"
    db.commit()
    db.refresh(schedule)
    return schedule
