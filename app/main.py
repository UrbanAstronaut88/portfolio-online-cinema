from fastapi import FastAPI

from app.routes.movies import router as movies_router
from app.routes.auth import router as auth_router
from app.routes.cart import router as cart_router
from app.routes.orders import router as orders_router
from app.routes.payments import router as payments_router
from app.routes.webhook import router as webhook_router
from app.routes.users import router as users_router
from app.routes.certifications import router as certifications_router
from dotenv import load_dotenv


load_dotenv()

app = FastAPI(
    title="Online Cinema API",
    description="Portfolio project: Online cinema backend with auth, cart, orders, payments, etc...\n"
    "\nauthor: UrbanAstronaut88",
    version="1.0.0",
)


# Routers ===
app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)
app.include_router(webhook_router)
app.include_router(users_router)
app.include_router(certifications_router)



@app.get("/")
def read_root():
    return {
        "module": "15, FastAPI and SQLAlchemy",
        "task": "Online Cinema Portfolio Project",
        "author": "UrbanAstronaut88@gmail.com",
    }
