from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.payments import Payment
from app.crud.payments import create_payment, get_payments
# current_user

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/{order_id}", response_model=dict)
def initiate_payment(order_id: int, db: Session = Depends(get_db)):
    # user_id = current_user.id, check ownership
    payment, client_secret = create_payment(db, order_id)
    if not payment:
        raise HTTPException(400, "Invalid order")
    return {"client_secret": client_secret}  # Для Stripe Elements на фронте

@router.get("/", response_model=List[Payment])
def read_payments(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    # Для пользователя: user_id = current_user.id
    # Для модератора: все с filters
    return get_payments(db, user_id=1, skip=skip, limit=limit)

# Добавь webhook endpoint для Stripe: @router.post("/webhook")
# В нём: event = stripe.Webhook.construct_event(...), if event.type == 'payment_intent.succeeded': confirm_payment