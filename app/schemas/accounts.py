from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from datetime import datetime
from enum import Enum
from typing import Optional
import re


# ============================================================
# ENUMS
# ============================================================

class UserGroupEnum(str, Enum):
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class GenderEnum(str, Enum):
    MAN = "MAN"
    WOMAN = "WOMAN"


# ============================================================
# PASSWORD VALIDATION (ONE PLACE)
# ============================================================

def validate_password_strength(password: str) -> str:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters")

    patterns = [
        (r"[A-Z]", "Password must contain at least one uppercase letter"),
        (r"[a-z]", "Password must contain at least one lowercase letter"),
        (r"\d", "Password must contain at least one digit"),
        (r"[!@#$%^&*(),.?\":{}|<>]", "Password must contain at least one special character"),
    ]
    for pattern, msg in patterns:
        if not re.search(pattern, password):
            raise ValueError(msg)

    return password


# ============================================================
# BASE SCHEMAS
# ============================================================

class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8)

    @field_validator("password")
    def strong_password(cls, v):
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar: Optional[str] = None
    gender: Optional[GenderEnum] = None
    date_of_birth: Optional[datetime] = None
    info: Optional[str] = None


# ============================================================
# OUTPUT SCHEMAS (USED IN RESPONSES)
# ============================================================

class UserOut(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    group: UserGroupEnum

    model_config = ConfigDict(from_attributes=True)

    # SQLAlchemy Enum → str
    @field_validator("group", mode="before")
    def convert_group(cls, value):
        if hasattr(value, "name"):
            return value.name
        return value


# ============================================================
# AUTH SCHEMAS
# ============================================================

class UserLoginResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    def strong_password(cls, v):
        return validate_password_strength(v)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    def strong_password(cls, v):
        return validate_password_strength(v)


# ============================================================
# ADMIN MODELS
# ============================================================

class ChangeUserRole(BaseModel):
    user_id: int
    new_role: UserGroupEnum


# ============================================================
# TOKENS
# ============================================================

class ActivationTokenBase(BaseModel):
    token: str
    expires_at: datetime


class ActivationToken(ActivationTokenBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class RefreshTokenBase(BaseModel):
    token: str
    expires_at: datetime


class RefreshToken(RefreshTokenBase):
    id: int
    user_id: int

    model_config = ConfigDict(from_attributes=True)
