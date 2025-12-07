from datetime import datetime

from sqlalchemy import update, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.orders import Order, OrderItem, OrderStatusEnum
from app.models.cart import CartItem
from app.crud.cart import get_cart_with_items, get_or_create_cart
from app.crud.payments import create_payment


async def create_order_from_cart(db: AsyncSession, user_id: int, initiate_payment: bool = True):
    # First, create a basket if there isn't one.
    cart = await get_or_create_cart(db, user_id)

    # Now we load the basket with items + movie via joinedload
    cart = await get_cart_with_items(db, cart.id)

    # Checking the basket
    if not cart.items:
        return None

    # Calculate the cost of your order
    total = sum(item.movie.price for item in cart.items)

    db_order = Order(user_id=user_id, total_amount=total)
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)

    # Create an OrderItem for each film
    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=db_order.id,
            movie_id=cart_item.movie_id,
            price_at_order=cart_item.movie.price,
        )
        db.add(order_item)

    await db.commit()

    # Empty the basket
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await db.commit()

    # We automatically create a payment (Stripe mock or custom logic)
    if initiate_payment:
        payment, client_secret = await create_payment(db, db_order.id)

    return db_order


async def get_orders(
    db: AsyncSession,
    user_id: int = None,
    status: OrderStatusEnum = None,
    start_date: datetime = None,
    end_date: datetime = None,
    skip: int = 0,
    limit: int = 10
):
    query = (
        select(Order)
        .options(
            joinedload(Order.items).joinedload(OrderItem.movie)
        )
    )

    if user_id:
        query = query.where(Order.user_id == user_id)
    if status:
        query = query.where(Order.status == status)
    if start_date:
        query = query.where(Order.created_at >= start_date)
    if end_date:
        query = query.where(Order.created_at <= end_date)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.unique().scalars().all()


async def cancel_order(db: AsyncSession, order_id: int, user_id: int):
    # Receiving an order
    result = await db.execute(
        select(Order)
        .options(joinedload(Order.items).joinedload(OrderItem.movie))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    order = result.scalars().first()

    # Checking whether it is possible to cancel
    if order and order.status == OrderStatusEnum.PENDING:
        order.status = OrderStatusEnum.CANCELED
        await db.commit()

        # We load the fresh order with items again
        refreshed = await db.execute(
            select(Order)
            .options(joinedload(Order.items).joinedload(OrderItem.movie))
            .where(Order.id == order_id)
        )
        return refreshed.scalars().first()

    return None


async def update_status(db: AsyncSession, order_id: int, new_status: OrderStatusEnum):
    await db.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(status=new_status)
    )
    await db.commit()
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalars().first()
