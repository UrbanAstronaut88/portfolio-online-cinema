from sqlalchemy.orm import Session
from app.models.accounts import User, UserGroup, ActivationToken
from app.schemas.accounts import UserCreate
from passlib.context import CryptContext
from datetime import timedelta, datetime
import uuid

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, group_id=1)  # Предполагаем group_id=1 для USER
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_activation_token(db: Session, user_id: int):
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=24)
    db_token = ActivationToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token

# Позже добавить функции для других: get_user_by_email, activate_user, etc.