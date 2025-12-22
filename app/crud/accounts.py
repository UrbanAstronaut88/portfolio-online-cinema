import re
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.models.accounts import User, UserGroup, ActivationToken, PasswordResetToken, RefreshToken, UserGroupEnum
from app.schemas.accounts import UserCreate
from passlib.context import CryptContext
from datetime import timedelta, datetime
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def check_password_complexity(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


async def get_user_by_email(db: AsyncSession, email: str) -> User:
    result = await db.execute(select(User).options(joinedload(User.group)).where(User.email == email))
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).options(joinedload(User.group)).where(User.id == user_id))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: UserCreate):
    if not check_password_complexity(user.password):
        raise ValueError("Password does not meet complexity requirements")

    existing_user = await get_user_by_email(db, user.email)
    if existing_user:
        raise ValueError("Email already registered")

    result = await db.execute(
        select(UserGroup).where(UserGroup.name == UserGroupEnum.USER)
    )
    user_group = result.scalar_one()

    hashed_password = get_password_hash(user.password)

    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        group_id=user_group.id,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    result = await db.execute(
        select(User)
        .options(joinedload(User.group))
        .where(User.id == db_user.id)
    )
    user_with_group = result.scalars().first()

    return user_with_group


async def create_activation_token(db: AsyncSession, user_id: int):
    await db.execute(delete(ActivationToken).where(ActivationToken.user_id == user_id))
    await db.commit()

    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)
    db_token = ActivationToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def activate_user(db: AsyncSession, token: str) -> bool:
    result = await db.execute(select(ActivationToken).where(ActivationToken.token == token))
    activation_token = result.scalars().first()
    if not activation_token or activation_token.expires_at < datetime.utcnow():
        return False
    user = await get_user_by_id(db, activation_token.user_id)
    if user:
        user.is_active = True
        await db.delete(activation_token)
        await db.commit()
        return True
    return False


async def change_password(db: AsyncSession, user_id: int, old_password: str, new_password: str):
    user = await get_user_by_id(db, user_id)
    if not user or not verify_password(old_password, user.hashed_password):
        raise ValueError("Invalid old password")
    if not check_password_complexity(new_password):
        raise ValueError("New password does not meet complexity requirements")
    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    return True


async def request_password_reset(db: AsyncSession, email: str):
    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)
    db_token = PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at)
    db.add(db_token)
    await db.commit()
    await db.refresh(db_token)
    return db_token


async def reset_password(db: AsyncSession, token: str, new_password: str):
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token == token))
    reset_token = result.scalars().first()
    if not reset_token or reset_token.expires_at < datetime.utcnow():
        return False
    user = await get_user_by_id(db, reset_token.user_id)
    if user:
        if not check_password_complexity(new_password):
            raise ValueError("New password does not meet complexity requirements")
        user.hashed_password = get_password_hash(new_password)
        await db.delete(reset_token)
        await db.commit()
        return True
    return False


async def logout(db: AsyncSession, refresh_token: str):
    result = await db.execute(select(RefreshToken).where(RefreshToken.token == refresh_token))
    db_token = result.scalars().first()
    if db_token:
        await db.delete(db_token)
        await db.commit()
        return True
    return False


async def set_user_role(db: AsyncSession, user_id: int, new_role: str):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise ValueError("User not found")

    result = await db.execute(
        select(UserGroup).where(UserGroup.name == new_role)
    )
    group = result.scalars().first()

    if not group:
        raise ValueError("Invalid role")

    user.group_id = group.id
    await db.commit()
    await db.refresh(user)

    return user
