from pydantic import BaseModel, EmailStr, Field


class TeacherRegister(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)


class TeacherLogin(BaseModel):
    username: str
    password: str


class TeacherRead(BaseModel):
    id: int
    username: str
    display_name: str
    email: str | None
    phone: str | None
    status: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    teacher: TeacherRead
