from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.core.pagination import Page, PageParams
from app.core.status import ResourceStatus
from app.models import Class, Teacher
from app.modules.classes.schemas import ClassCreate, ClassRead, ClassUpdate
from app.modules.classes.service import (
    create_class,
    delete_class,
    get_class,
    list_classes,
    update_class,
)

router = APIRouter(prefix="/classes", tags=["classes"])


@router.get("", response_model=Page[ClassRead])
def list_(
    params: PageParams = Depends(),
    keyword: str | None = None,
    status: ResourceStatus | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    items, total = list_classes(db, current_teacher, params.page, params.page_size, keyword, status)
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}


@router.post("", response_model=ClassRead, status_code=201)
def create(
    payload: ClassCreate,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Class:
    return create_class(db, current_teacher, payload)


@router.get("/{class_id}", response_model=ClassRead)
def get(
    class_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Class:
    return get_class(db, current_teacher, class_id)


@router.patch("/{class_id}", response_model=ClassRead)
def update(
    payload: ClassUpdate,
    class_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Class:
    return update_class(db, current_teacher, class_id, payload)


@router.delete("/{class_id}", response_model=ClassRead)
def delete(
    class_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> Class:
    return delete_class(db, current_teacher, class_id)
