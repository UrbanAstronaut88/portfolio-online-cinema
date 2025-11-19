from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.routes.movies import router as movies_router
from app.routes.auth import router as auth_router
from app.routes.cart import router as cart_router
from app.routes.orders import router as orders_router
from app.db.session import get_db
from app.models.accounts import User

app = FastAPI()

app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(cart_router)
app.include_router(orders_router)


@app.get("/")
def read_root():
    return {"message": "FastAPI Online-Cinema"}


@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()
