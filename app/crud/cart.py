from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate
from app.models.movies import Movie

async def get_or_create_cart(db: AsyncSession, user_id: int):
    result = await db.execute(select(Cart).where(Cart.user_id == user_id))
    cart = result.scalars().first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    return cart

async def add_item_to_cart(db: AsyncSession, cart_id: int, item: CartItemCreate):
    result = await db.execute(select(CartItem).where(CartItem.cart_id == cart_id, CartItem.movie_id == item.movie_id))
    existing = result.scalars().first()
    if existing:
        return None
    db_item = CartItem(cart_id=cart_id, movie_id=item.movie_id)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item

async def remove_item_from_cart(db: AsyncSession, item_id: int):
    result = await db.execute(select(CartItem).where(CartItem.id == item_id))
    item = result.scalars().first()
    if item:
        await db.delete(item)
        await db.commit()
    return item

async def clear_cart(db: AsyncSession, cart_id: int):
    await db.execute(delete(CartItem).where(CartItem.cart_id == cart_id))
    await db.commit()

async def get_cart_with_items(db: AsyncSession, cart_id: int):
    result = await db.execute(
        select(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.movie))
        .where(Cart.id == cart_id)
    )
    cart = result.scalars().first()
    if not cart:
        raise ValueError("Cart not found")
    return cart
