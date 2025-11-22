from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.schemas.payments import Payment
from app.crud.payments import create_payment, get_payments
import stripe

from app.utils.email import send_email

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
@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = "your_webhook_secret"   # from Stripe dashboard

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]
        payment_id = payment_intent["id"]

        # запускаем в фоне что бы не блочить webhook
        background_tasks.add_task(create_payment, db, payment_id)

    return {"status": "success"}


"""тест роутер"""
@router.get("/test-email")
async def test_email():
    await send_email("Test Subject", ["urbanastronaut88@gmail.com"], "This is a test email.")
    return {"message": "Email sent!"}
