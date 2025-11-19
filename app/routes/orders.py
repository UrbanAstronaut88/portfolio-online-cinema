from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.orders import Order
from app.crud.orders import create_order_from_cart, get_orders, cancel_order
from app.crud.payments import create_payment

# current_user

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=dict)
def create_order(db: Session = Depends(get_db)):
    # user_id = current_user.id  # в будущем заменить на аутентифицированного пользователя
    order = create_order_from_cart(db, user_id=1)  # создаём заказ из корзины (без автоматической инициации платежа)
    if not order:
        raise HTTPException(400, "Cart is empty or invalid items")

    # инициируем платёж сразу после создания заказа
    payment, client_secret = create_payment(db, order.id)
    if not payment:
        raise HTTPException(400, "Failed to initiate payment")

    return {"order_id": order.id, "client_secret": client_secret}  # возвращаем для фронтенда (Stripe Elements)


@router.get("/", response_model=List[Order])
def read_orders(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # для пользователя: user_id = current_user.id
    # для модератора: все
    return get_orders(db, user_id=1, skip=skip, limit=limit)


@router.post("/{order_id}/cancel", response_model=Order)
def cancel(order_id: int, db: Session = Depends(get_db)):
    canceled = cancel_order(db, order_id)
    if not canceled:
        raise HTTPException(400, "Cannot cancel or order not found")
    return canceled

# добавить /pay (redirect to Stripe, позже), filters