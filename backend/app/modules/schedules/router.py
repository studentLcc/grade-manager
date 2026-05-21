from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.core.pagination import Page, PageParams
from app.core.status import ResourceStatus
from app.models import Schedule, Teacher
from app.modules.schedules.schemas import ScheduleCreate, ScheduleRead, ScheduleUpdate
from app.modules.schedules.service import (
    create_schedule,
    delete_schedule,
    get_schedule,
    list_schedules,
    update_schedule,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=Page[ScheduleRead])
def list_(
    params: PageParams = Depends(),
    keyword: str | None = None,
    status: ResourceStatus | None = None,
    class_id: int | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    items, total = list_schedules(
        db,
        current_teacher,
        params.page,
        params.page_size,
        keyword,
        status,
        class_id,
    )
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}


@router.post("", response_model=ScheduleRead, status_code=201)
def create(
    payload: ScheduleCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Schedule:
    return create_schedule(db, current_teacher, payload)


@router.get("/{schedule_id}", response_model=ScheduleRead)
def get(
    schedule_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Schedule:
    return get_schedule(db, current_teacher, schedule_id)


@router.patch("/{schedule_id}", response_model=ScheduleRead)
def update(
    payload: ScheduleUpdate,
    schedule_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Schedule:
    return update_schedule(db, current_teacher, schedule_id, payload)


@router.delete("/{schedule_id}", response_model=ScheduleRead)
def delete(
    schedule_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Schedule:
    return delete_schedule(db, current_teacher, schedule_id)
