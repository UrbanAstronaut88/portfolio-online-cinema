# app/crud/orders.py (обновлённый для async, production-ready, добавлены update_status и filters)
from datetime import datetime

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from app.models.orders import Order, OrderItem, OrderStatusEnum
from app.schemas.orders import OrderCreate
from app.crud.cart import get_or_create_cart
from app.models.cart import CartItem
from app.crud.payments import create_payment


async def create_order_from_cart(db: AsyncSession, user_id: int, initiate_payment: bool = True):
    cart = await get_or_create_cart(db, user_id)
    if not cart.items:
        return None # empty the basket

    # Calculate the amount asynchronously (items already loaded)
    total = sum(item.movie.price for item in cart.items)
    db_order = Order(user_id=user_id, total_amount=total)
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)

    for cart_item in cart.items:
        db_item = OrderItem(order_id=db_order.id, movie_id=cart_item.movie_id, price_at_order=cart_item.movie.price)
        db.add(db_item)
    await db.commit()

    # empty the basket
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await db.commit()

    if initiate_payment:
        payment, client_secret = await create_payment(db, db_order.id)
        # Here you can return client_secret for the front end, but in crud we return order.
        # in reality: process in the router
    return db_order


async def get_orders(db: AsyncSession, user_id: int = None, status: OrderStatusEnum = None, start_date: datetime = None, end_date: datetime = None, skip: int = 0, limit: int = 10):
    query = select(Order).options(joinedload(Order.items))
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
    return result.scalars().all()


async def cancel_order(db: AsyncSession, order_id: int, user_id: int):
    result = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user_id))
    order = result.scalars().first()
    if order and order.status == OrderStatusEnum.PENDING:
        order.status = OrderStatusEnum.CANCELED
        await db.commit()
        await db.refresh(order)
        return order
    return None


async def update_status(db: AsyncSession, order_id: int, new_status: OrderStatusEnum):
    # For payment or other changes (e.g. from webhook)
    await db.execute(
        update(Order)
        .where(Order.id == order_id)
        .values(status=new_status)
    )
    await db.commit()
    result = await db.execute(select(Order).where(Order.id == order_id))
    return result.scalars().first()