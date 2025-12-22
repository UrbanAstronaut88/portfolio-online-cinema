from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.accounts import User
from app.schemas.accounts import (
    UserCreate,
    UserOut,
    UserLoginResponseSchema,
    PasswordChange,
    ChangeUserRole
)
from app.crud.accounts import (
    create_user,
    create_activation_token,
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


@router.post(
    "/register",
    response_model=UserOut,
    summary="Register a new user",
    description=(
        "Creates a new user account.\n\n"
        "- Validates password complexity\n"
        "- Sends an activation email\n"
        "- Account must be activated before login"
    ),
    responses={
        200: {"description": "User successfully registered"},
        400: {"description": "Validation error or email already exists"},
    },
)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_user = await create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = await create_activation_token(db, db_user.id)

    await send_email(
        "Activate your account",
        [user.email],
        f"http://localhost:8000/auth/activate/{token.token}",
    )

    return UserOut.model_validate(db_user)


@router.get(
    "/activate/{token}",
    summary="Activate user account",
    description="Activates user account using activation token from email.",
    responses={
        200: {"description": "Account activated"},
        400: {"description": "Invalid or expired token"},
    },
)
async def activate(token: str, db: AsyncSession = Depends(get_db)):
    activated = await activate_user(db, token)
    if not activated:
        raise HTTPException(status_code=400, detail="Invalid or expired activation token")
    return {"message": "Account activated"}


@router.post(
    "/login",
    response_model=UserLoginResponseSchema,
    summary="Login user",
    description=(
        "Authenticates user using email and password.\n\n"
        "Returns access and refresh tokens."
    ),
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        403: {"description": "Account not activated"},
    },
)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    email = form_data.username

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=401, detail="User with this email not found")

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account not activated")

    refresh = await create_refresh_token(user.id, db)
    access = await create_access_token({"sub": user.email})

    return UserLoginResponseSchema(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
    )


@router.post(
    "/logout",
    summary="Logout user",
    description="Invalidates refresh token.",
    responses={
        200: {"description": "Logged out"},
        400: {"description": "Invalid refresh token"},
    },
)
async def logout_user(refresh_token: str, db: AsyncSession = Depends(get_db)):
    success = await logout(db, refresh_token)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    return {"message": "Logged out successfully"}


@router.post(
    "/password/change",
    summary="Change password",
    description="Changes password for authenticated user.",
    responses={
        200: {"description": "Password changed"},
        400: {"description": "Invalid old password or validation error"},
        401: {"description": "Not authenticated"},
    },
)
async def change_user_password(
    data: PasswordChange = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await change_password(db, current_user.id, data.old_password, data.new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Password changed successfully"}


@router.post(
    "/password/reset/request",
    summary="Request password reset",
    description="Sends password reset email if user exists.",
)
async def request_reset(email: str, db: AsyncSession = Depends(get_db)):
    token = await request_password_reset(db, email)
    if token:
        await send_email(
            "Password Reset",
            [email],
            f"http://localhost:8000/auth/password/reset/{token.token}",
        )
    return {"message": "If the email is registered, a reset link has been sent"}


@router.post(
    "/password/reset/{token}",
    summary="Reset password",
    description="Resets password using reset token.",
)
async def reset_user_password(token: str, new_password: str, db: AsyncSession = Depends(get_db)):
    success = await reset_password(db, token, new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"message": "Password reset successfully"}


@router.post(
    "/set-role",
    summary="Change user role",
    description="Allows ADMIN to change user role.",
    responses={
        200: {"description": "Role updated"},
        403: {"description": "Not authorized"},
    },
)
async def change_user_role(
    data: ChangeUserRole,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.group.name != "ADMIN":
        raise HTTPException(403, "You are not allowed to change roles")

    updated = await set_user_role(db, data.user_id, data.new_role.value)
    return {
        "message": f"Role changed successfully to {data.new_role}",
        "user_id": updated.id,
        "new_role": updated.group.name,
    }
