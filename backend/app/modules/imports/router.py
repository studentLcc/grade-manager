from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.core.pagination import Page, PageParams
from app.models import Teacher
from app.modules.imports.schemas import ImportBatchRead, ImportErrorRead
from app.modules.imports.service import get_import_batch, list_import_batches, list_import_errors

router = APIRouter(prefix="/imports", tags=["imports"])


@router.get("", response_model=Page[ImportBatchRead])
def list_(
    params: PageParams = Depends(),
    import_type: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    items, total = list_import_batches(
        db,
        current_teacher,
        params.page,
        params.page_size,
        import_type,
        status,
        keyword,
    )
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}


@router.get("/{batch_id}", response_model=ImportBatchRead)
def get(
    batch_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    return get_import_batch(db, current_teacher, batch_id)


@router.get("/{batch_id}/errors", response_model=Page[ImportErrorRead])
def errors(
    params: PageParams = Depends(),
    batch_id: int = Path(gt=0),
    db: Session = Depends(get_db),
    current_teacher: Teacher = Depends(get_current_teacher),
) -> dict[str, object]:
    items, total = list_import_errors(db, current_teacher, batch_id, params.page, params.page_size)
    return {"items": items, "total": total, "page": params.page, "page_size": params.page_size}
