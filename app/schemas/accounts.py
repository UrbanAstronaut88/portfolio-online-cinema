from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from enum import Enum
from typing import Optional
import re

class UserGroupEnum(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class GenderEnum(str, Enum):
    MAN = "MAN"
    WOMAN = "WOMAN"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)  # Базовая проверка длины

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


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

    @classmethod
    def model_validate(cls, obj):
        try:
            group_name = obj.group.name if getattr(obj, "group", None) is not None else None
        except Exception:
            group_name = None

        if group_name is None:
            group_name = UserGroupEnum.USER.value

        return cls(
            id=obj.id,
            email=obj.email,
            is_active=obj.is_active,
            group=group_name,
        )


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class ActivationTokenCreate(BaseModel):
    token: str
    expires_at: datetime


class ActivationToken(ActivationTokenCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)

    @validator("new_password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class RefreshTokenCreate(BaseModel):
    token: str
    expires_at: datetime


class RefreshToken(RefreshTokenCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True
