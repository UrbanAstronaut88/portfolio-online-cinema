from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum
from typing import Optional


class UserGroupEnum(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class GenderEnum(str, Enum):
    MAN = "MAN"
    WOMAN = "WOMAN"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)  # Проверка сложности можно добавить позже <<<<<<<<<<<<<<<<<<<<


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[datetime] = None
    info: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    group: UserGroupEnum


    class Config:
        from_attributes = True  # Для ORM


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

# Аналогично для других: ActivationTokenCreate, etc.
