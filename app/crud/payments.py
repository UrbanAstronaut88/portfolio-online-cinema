import os
from sqlalchemy.orm import Session
from app.models.payments import Payment, PaymentItem, PaymentStatusEnum
from app.models.orders import Order, OrderStatusEnum, OrderItem
from app.schemas.payments import PaymentCreate
from app.utils.email import send_email
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_API_KEY")


def create_payment(db: Session, order_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order or order.status != OrderStatusEnum.PENDING:
        return None

    # создать Stripe payment intent
    intent = stripe.PaymentIntent.create(
        amount=int(order.total_amount * 100),  # в центах
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
    db.commit()
    db.refresh(db_payment)

    for order_item in order.items:
        db_item = PaymentItem(payment_id=db_payment.id, order_item_id=order_item.id,
                              price_at_payment=order_item.price_at_order)
        db.add(db_item)
    db.commit()

    return db_payment, intent.client_secret  # для фронта


async def confirm_payment(db: Session, payment_id: str):
    payment = db.query(Payment).filter(Payment.external_payment_id == payment_id).first()
    if payment:
        payment.status = PaymentStatusEnum.SUCCESSFUL
        order = payment.order
        order.status = OrderStatusEnum.PAID
        db.commit()

        # отправить email подтверждение
        user_email = order.user.email  # предполагаем, что в Order.user есть email
        body = f"Order: {order.id}, Total: {payment.amount} USD."
        await send_email("Confirmation of payment", [user_email], body)

    return payment


def get_payments(db: Session, user_id: int = None, skip: int = 0, limit: int = 10):
    query = db.query(Payment)
    if user_id:
        query = query.filter(Payment.user_id == user_id)
    return query.offset(skip).limit(limit).all()

# позже добавить refund, filters