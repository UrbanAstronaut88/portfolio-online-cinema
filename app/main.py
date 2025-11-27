from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer

from app.routes.movies import router as movies_router
from app.routes.auth import router as auth_router
from app.routes.cart import router as cart_router
from app.routes.orders import router as orders_router
from app.routes.payments import router as payments_router

from app.db.session import get_db
from app.models.accounts import User


# этот oauth2_scheme используется в коде (get_current_user и т.п.)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


app = FastAPI(
    title="Online Cinema API",
    description="Portfolio project: Online cinema backend with auth, cart, orders, payments",
    version="1.0.0",
)

app.openapi_schema = None  # чтобы гарантированно пересоздать схему


# Routers
app.include_router(auth_router)
app.include_router(movies_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(payments_router)


# Base endpoints
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


# Custom OpenAPI: одновременно объявляем OAuth2 password flow и HTTP Bearer
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Добавляем обе схемы: OAuth2 (password) и HTTP Bearer
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2Password": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/login",
                    "scopes": {}
                }
            }
        },
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # По умолчанию указываем, что защищённые методы используют BearerAuth.
    # (Если хочешь чтобы Swagger автоматически получал токен по username/password,
    #  можно менять это поведение — сейчас основным используем Bearer.)
    for path_item in openapi_schema["paths"].values():
        for operation in path_item.values():
            # не переписываем security, если оно уже задано явно
            operation.setdefault("security", [{"BearerAuth": []}])

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi
