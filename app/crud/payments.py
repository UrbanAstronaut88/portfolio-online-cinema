import os
import stripe

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models.payments import Payment, PaymentItem, PaymentStatusEnum
from app.models.orders import Order, OrderStatusEnum, OrderItem
from app.utils.email import send_email
from datetime import datetime


MOCK_MODE = os.getenv("MOCK_MODE", False) == "True"
stripe.api_key = os.getenv("STRIPE_API_KEY")


async def create_payment(db: AsyncSession, order_id: int):
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order or order.status != OrderStatusEnum.PENDING:
        return None

    # create a Stripe payment intent
    intent = stripe.PaymentIntent.create(
        amount=int(order.total_amount * 100),  # pence
        currency="usd",
        metadata={"order_id": order_id}
    )

    db_payment = Payment(
        user_id=order.user_id,
        order_id=order_id,
        amount=order.total_amount,
        external_payment_id=intent.id
    )
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)

    result_items = await db.execute(select(OrderItem).where(OrderItem.order_id == order_id))
    order_items = result_items.scalars().all()
    for order_item in order_items:
        db_item = PaymentItem(payment_id=db_payment.id, order_item_id=order_item.id,
                              price_at_payment=order_item.price_at_order)
        db.add(db_item)
    await db.commit()

    return db_payment, intent.client_secret  # for the front


async def confirm_payment(db: AsyncSession, payment_id: str):
    result = await db.execute(select(Payment).where(Payment.external_payment_id == payment_id))
    payment = result.scalars().first()
    if payment:
        payment.status = PaymentStatusEnum.SUCCESSFUL
        order = payment.order
        order.status = OrderStatusEnum.PAID
        await db.commit()

        # send confirmation email
        user_email = order.user.email  # We assume that Order.user contains an email address.
        body = f"Order: {order.id}, Total: {payment.amount} USD."
        await send_email("Confirmation of payment", [user_email], body)

    return payment


async def refund_payment(db, payment_id: int):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalars().first()

    if not payment:
        return None

    # ---------- MOCK MODE (NO STRIPE) ----------
    if MOCK_MODE:
        payment.status = PaymentStatusEnum.REFUNDED
        await db.commit()
        await db.refresh(payment)
        return payment

    # ---------- REAL STRIPE MODE ----------
    try:
        if not payment.external_payment_id:
            raise ValueError("No external payment id")

        pi = stripe.PaymentIntent.retrieve(payment.external_payment_id)

        refund = stripe.Refund.create(payment_intent=pi.id)

        payment.status = PaymentStatusEnum.REFUNDED
        await db.commit()
        await db.refresh(payment)
        return payment

    except Exception as e:
        raise ValueError(f"Stripe refund failed: {str(e)}")


async def get_payments(
    db: AsyncSession,
    user_id: int = None,
    status: PaymentStatusEnum = None,
    start_date: datetime = None,
    end_date: datetime = None,
    skip: int = 0,
    limit: int = 10
):
    query = select(Payment).options(joinedload(Payment.items), joinedload(Payment.order))
    if user_id:
        query = query.where(Payment.user_id == user_id)
    if status:
        query = query.where(Payment.status == status)
    if start_date:
        query = query.where(Payment.created_at >= start_date)
    if end_date:
        query = query.where(Payment.created_at <= end_date)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.unique().scalars().all()
