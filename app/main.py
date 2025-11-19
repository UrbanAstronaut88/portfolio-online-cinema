from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.routes.movies import router as movies_router
from app.routes.auth import router as auth_router
from app.routes.cart import router as cart_router
from app.routes.orders import router as orders_router
from app.routes.payments import router as payments_router
from app.db.session import get_db
from app.models.accounts import User

app = FastAPI()

app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)

@app.get("/")
def read_root():
    return {
        "module": "15, FastAPI and SQLAlchemy",
        "task": "Online Cinema Portfolio Project",
        "author": "urbanastronaut88",
    }


@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
