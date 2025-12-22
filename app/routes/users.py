from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.accounts import User, UserGroupEnum
from app.schemas.users import UserListResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=UserListResponse,
    summary="List users",
    description=(
        "Returns list of users.\n\n"
        "- ADMIN only\n"
        "- Supports filtering by email and role\n"
        "- Supports pagination"
    ),
)
async def list_users(
    skip: int = 0,
    limit: int = 10,
    email: str | None = None,
    group: UserGroupEnum | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.group.name != "ADMIN":
        raise HTTPException(403, "Only admin can access users list")

    query = select(User).options(selectinload(User.group))
    count_query = select(func.count(User.id))

    if email:
        query = query.where(User.email.ilike(f"%{email}%"))
        count_query = count_query.where(User.email.ilike(f"%{email}%"))

    if group:
        query = query.where(User.group.has(name=group))
        count_query = count_query.where(User.group.has(name=group))

    query = query.offset(skip).limit(limit)

    total = (await db.execute(count_query)).scalar_one()
    users = (await db.execute(query)).scalars().all()

    return UserListResponse(total=total, users=users)
