from pydantic import BaseModel, field_validator, ConfigDict
from enum import Enum
from typing import List


class UserGroupEnum(str, Enum):
    ADMIN = "ADMIN"
    MODERATOR = "MODERATOR"
    USER = "USER"


class UserSchema(BaseModel):
    id: int
    email: str
    group: UserGroupEnum

    model_config = ConfigDict(from_attributes=True)

    @field_validator("group", mode="before")
    def convert_group(cls, value):
        # SQLAlchemy Enum -> string
        if hasattr(value, "name"):
            return value.name
        return value


class UserListResponse(BaseModel):
    total: int
    users: List[UserSchema]
