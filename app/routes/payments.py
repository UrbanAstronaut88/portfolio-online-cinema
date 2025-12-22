from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.models.orders import Order
from app.models.payments import Payment, PaymentStatusEnum
from app.schemas.payments import Payment as PaymentSchema
from app.crud.payments import create_payment, get_payments, refund_payment
from app.utils.auth import get_current_user
from app.models.accounts import User, UserGroupEnum


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post(
    "/{order_id}",
    response_model=dict,
    summary="Create payment for order",
    description="Creates a payment intent for a specific order owned by the user.",
)
async def initiate_payment(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order_result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    order = order_result.scalars().first()

    if not order:
        raise HTTPException(403, "Not authorized or order not found")

    payment, client_secret = await create_payment(db, order_id)
    if not payment:
        raise HTTPException(400, "Invalid order")

    return {"client_secret": client_secret}


@router.get(
    "/",
    response_model=List[PaymentSchema],
    summary="Get payments",
    description=(
        "Returns payments list.\n\n"
        "- Users see only their own payments\n"
        "- Admins and moderators see all payments\n"
        "- Supports filters and pagination"
    ),
)
async def read_payments(
    skip: int = 0,
    limit: int = 10,
    status: PaymentStatusEnum = None,
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = (
        current_user.id
        if current_user.group.name not in [UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN]
        else None
    )
    return await get_payments(
        db,
        user_id=user_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/{payment_id}/refund",
    summary="Refund payment",
    description="ADMIN and MODERATOR only. Refunds a payment.",
)
async def refund(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.group.name not in [UserGroupEnum.MODERATOR, UserGroupEnum.ADMIN]:
        raise HTTPException(403, "Not authorized")

    refunded = await refund_payment(db, payment_id)
    if not refunded:
        raise HTTPException(400, "Cannot refund or payment not found")

    return {"message": "Refund processed"}


@router.post(
    "/mock_success/{payment_id}",
    summary="Mock payment success",
    description=(
        "Simulates successful Stripe payment.\n\n"
        "ADMIN and MODERATOR only.\n"
        "Used for testing and development."
    ),
)
async def mock_payment_success(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.group.name not in ["ADMIN", "MODERATOR"]:
        raise HTTPException(403, "Not authorized")

    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalars().first()

    if not payment:
        raise HTTPException(404, "Payment not found")

    payment.status = PaymentStatusEnum.SUCCESSFUL
    await db.commit()
    await db.refresh(payment)

    return {"message": f"Payment {payment_id} marked as SUCCESSFUL"}
