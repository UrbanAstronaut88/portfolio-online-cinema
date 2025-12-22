from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.models.orders import Order, OrderStatusEnum
from app.schemas.orders import Order as OrderSchema
from app.crud.orders import create_order_from_cart, get_orders, cancel_order
from app.crud.payments import create_payment
from app.utils.auth import get_current_user
from app.models.accounts import User

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "/",
    response_model=dict,
    summary="Create order from cart",
    description=(
        "Creates an order based on the user's cart.\n\n"
        "- Cart must not be empty\n"
        "- Payment intent is created immediately"
    ),
)
async def create_order(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await create_order_from_cart(db, current_user.id)
    if not order:
        raise HTTPException(400, "Cart is empty or invalid items")

    payment, client_secret = await create_payment(db, order.id)
    if not payment:
        raise HTTPException(400, "Failed to initiate payment")

    return {"order_id": order.id, "client_secret": client_secret}


@router.get(
    "/",
    response_model=List[OrderSchema],
    summary="Get orders",
    description=(
        "Returns orders list.\n\n"
        "- Users see only their own orders\n"
        "- Admins and moderators can see all orders\n"
        "- Supports filtering and pagination"
    ),
)
async def read_orders(
    skip: int = 0,
    limit: int = 10,
    status: OrderStatusEnum = None,
    start_date: datetime = None,
    end_date: datetime = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_id = (
        current_user.id
        if current_user.group.name not in ["MODERATOR", "ADMIN"]
        else None
    )
    return await get_orders(
        db,
        user_id=user_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/{order_id}/cancel",
    response_model=OrderSchema,
    summary="Cancel order",
    description=(
        "Cancels an order.\n\n"
        "- Only allowed for PENDING orders\n"
        "- Only order owner can cancel"
    ),
)
async def cancel(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    canceled = await cancel_order(db, order_id, current_user.id)
    if not canceled:
        raise HTTPException(400, "Cannot cancel or order not found")
    return canceled


@router.post(
    "/{order_id}/pay",
    response_model=dict,
    summary="Initiate payment for order",
    description="Creates a payment intent for an existing PENDING order.",
)
async def pay_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id,
        )
    )
    order = order.scalars().first()

    if not order or order.status != OrderStatusEnum.PENDING:
        raise HTTPException(400, "Invalid order for payment")

    payment, client_secret = await create_payment(db, order_id)
    if not payment:
        raise HTTPException(400, "Failed to initiate payment")

    return {"client_secret": client_secret}
