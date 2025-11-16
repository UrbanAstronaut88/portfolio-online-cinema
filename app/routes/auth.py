from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.accounts import User
from app.schemas.accounts import UserCreate, UserOut, Token
from app.crud.accounts import create_user, create_activation_token, verify_password
from app.utils.auth import create_access_token, create_refresh_token
from app.utils.email import send_email


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = create_user(db, user)
    token = create_activation_token(db, db_user.id)
    # Отправка email
    await send_email("Activate your account", [user.email], f"Click to activate: http://localhost:8000/activate/{token.token}")
    return db_user


@router.get("/activate/{token}")
async def activate(token: str, db: Session = Depends(get_db)):
    # Найти токен, проверить expires, активировать user.is_active = True
    # Реализуй логику
    return {"message": "Account activated"}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Проверить email/password, выдать tokens
    # Реализуй: user = get_user_by_email, verify_password
    # Пример (добавь реальную проверку):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    access_token = create_access_token({"sub": user.email})
    refresh_token = create_refresh_token(user.id, db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


# Добавь /logout, /reset-password, etc.