from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_teacher
from app.models import Teacher
from app.modules.auth.schemas import TeacherLogin, TeacherRead, TeacherRegister, TokenResponse
from app.modules.auth.service import login_teacher, register_teacher

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TeacherRead, status_code=201)
def register(payload: TeacherRegister, db: Session = Depends(get_db)) -> Teacher:
    return register_teacher(db, payload)


@router.post("/login", response_model=TokenResponse)
def login(payload: TeacherLogin, db: Session = Depends(get_db)) -> TokenResponse:
    return login_teacher(db, payload)


@router.get("/me", response_model=TeacherRead)
def me(current_teacher: Teacher = Depends(get_current_teacher)) -> Teacher:
    return current_teacher
