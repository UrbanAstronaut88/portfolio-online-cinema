from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
from app.db.session import get_db
from app.models.orders import Order
from app.schemas.payments import Payment, PaymentStatusEnum
from app.crud.payments import create_payment, get_payments, confirm_payment, refund_payment
import stripe
import os
from dotenv import load_dotenv
from app.utils.auth import get_current_user
from app.models.accounts import User, UserGroupEnum
from app.utils.email import send_email

load_dotenv()

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/{order_id}", response_model=dict)
async def initiate_payment(order_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # check ownership
    order_result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == current_user.id))
    order = order_result.scalars().first()
    if not order:
        raise HTTPException(403, "Not authorized or order not found")
    payment, client_secret = await create_payment(db, order_id)
    if not payment:
        raise HTTPException(400, "Invalid order")
    return {"client_secret": client_secret}  # For Stripe Elements on the front end

@router.get("/", response_model=List[Payment])
async def read_payments(
    skip: int = 0,
    limit: int = 10,
    status: PaymentStatusEnum = None,
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # For users: only their own; for mod/admin: all with filters
    user_id = current_user.id if current_user.group.name not in [UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN] else None
    return await get_payments(db, user_id=user_id, status=status, start_date=start_date, end_date=end_date, skip=skip, limit=limit)

@router.post("/{payment_id}/refund")
async def refund(payment_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # For mod/admin only
    if current_user.group.name not in [UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN]:
        raise HTTPException(403, "Not authorized")
    refunded = await refund_payment(db, payment_id)
    if not refunded:
        raise HTTPException(400, "Cannot refund or payment not found")
    return {"message": "Refund processed"}

@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

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

        # run in the background so as not to block the webhook
        background_tasks.add_task(confirm_payment, db, payment_id)

    return {"status": "success"}


@router.get("/test-email")
async def test_email():
    await send_email("Test Subject", ["urbanastronaut88@gmail.com"], "This is a test email.")
    return {"message": "Email sent!"}