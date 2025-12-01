from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.accounts import User, RefreshToken
from app.schemas.accounts import UserCreate, UserOut, UserLoginResponseSchema, PasswordChange, ChangeUserRole
from app.crud.accounts import (
    create_user,
    create_activation_token,
    get_user_by_email,
    verify_password,
    activate_user,
    logout,
    request_password_reset,
    reset_password,
    change_password,
    set_user_role
)
from app.utils.auth import create_access_token, create_refresh_token, get_current_user
from app.utils.email import send_email



router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    db_user = await create_user(db, user)
    token = await create_activation_token(db, db_user.id)
    # sending email
    await send_email(
        "Activate your account",
        [user.email],
        f"Click to activate: http://localhost:8000/auth/activate/{token.token}"
    )
    return UserOut.model_validate(db_user)


@router.get("/activate/{token}")
async def activate(token: str, db: AsyncSession = Depends(get_db)):
    activated = await activate_user(db, token)
    if not activated:
        raise HTTPException(status_code=400, detail="Invalid or expired activation token")
    return {"message": "Account activated"}


@router.post("/login", response_model=UserLoginResponseSchema)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> UserLoginResponseSchema:

    email = form_data.username

    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User with this email not found"
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not activated"
        )

    refresh = await create_refresh_token(user.id, db)
    access = await create_access_token({"sub": user.email})

    return UserLoginResponseSchema(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer"
    )


@router.post("/logout")
async def logout_user(refresh_token: str, db: AsyncSession = Depends(get_db)):
    success = await logout(db, refresh_token)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    return {"message": "Logged out successfully"}


@router.post("/password/change")
async def change_user_password(
    data: PasswordChange = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        await change_password(db, current_user.id, data.old_password, data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Password changed successfully"}


@router.post("/password/reset/request")
async def request_reset(email: str, db: AsyncSession = Depends(get_db)):
    token = await request_password_reset(db, email)
    if token:
        await send_email("Password Reset", [email], f"Click to reset: http://localhost:8000/auth/password/reset/{token.token}")
    return {"message": "If the email is registered, a reset link has been sent"}


@router.post("/password/reset/{token}")
async def reset_user_password(token: str, new_password: str, db: AsyncSession = Depends(get_db)):
    success = await reset_password(db, token, new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"message": "Password reset successfully"}


@router.post("/set-role")
async def change_user_role(
    data: ChangeUserRole,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # verification: only the admin can change the role
    if current_user.group.name != "ADMIN":
        raise HTTPException(403, "You are not allowed to change roles")

    try:
        updated = await set_user_role(db, data.user_id, data.new_role.value)
        return {
            "message": f"Role changed successfully to {data.new_role}",
            "user_id": updated.id,
            "new_role": updated.group.name,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
