from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.accounts import User
from app.schemas.accounts import UserCreate, UserOut, Token
from app.crud.accounts import create_user, create_activation_token, get_user_by_email, verify_password, activate_user, logout, request_password_reset, reset_password, change_password
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


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not activated")
    access_token = create_access_token({"sub": user.email})
    refresh_token = await create_refresh_token(user.id, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/logout")
async def logout_user(refresh_token: str, db: AsyncSession = Depends(get_db)):
    success = await logout(db, refresh_token)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    return {"message": "Logged out successfully"}


@router.post("/password/change")
async def change_user_password(old_password: str, new_password: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    try:
        await change_password(db, current_user.id, old_password, new_password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": "Password changed successfully"}


@router.post("/password/reset/request")
async def request_reset(email: str, db: AsyncSession = Depends(get_db)):
    token = await request_password_reset(db, email)
    if token:
        await send_email("Password Reset", [email], f"Click to reset: http://localhost:8000/auth/password/reset/{token.token}")
    return {"message": "If the email is registered, a reset link has been sent"}  # Без раскрытия существования email


@router.post("/password/reset/{token}")
async def reset_user_password(token: str, new_password: str, db: AsyncSession = Depends(get_db)):
    success = await reset_password(db, token, new_password)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    return {"message": "Password reset successfully"}