from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.cart import CartItem
from app.schemas.cart import Cart, CartItemCreate
from app.crud.cart import get_or_create_cart, add_item_to_cart, remove_item_from_cart, clear_cart, get_cart_with_items
from app.utils.auth import get_current_user
from app.models.accounts import User


router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=Cart)
async def get_cart(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart = await get_or_create_cart(db, current_user.id)
    return await get_cart_with_items(db, cart.id)  # return with details items


@router.post("/items", response_model=Cart)
async def add_item(item: CartItemCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart = await get_or_create_cart(db, current_user.id)
    added = await add_item_to_cart(db, cart.id, item)
    if not added:
        raise HTTPException(400, "Item already in cart or purchased")
    return await get_cart_with_items(db, cart.id)  # Returning the updated basket


@router.delete("/items/{item_id}", response_model=Cart)
async def remove_item(item_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Ownership check: first, find the item and verify that cart.user_id == current_user.id
    item = await db.execute(select(CartItem).where(CartItem.id == item_id))
    item = item.scalars().first()
    if not item:
        raise HTTPException(404, "Item not found")
    cart = await get_or_create_cart(db, current_user.id)
    if item.cart_id != cart.id:
        raise HTTPException(403, "Not authorized to remove this item")
    await remove_item_from_cart(db, item_id)
    return await get_cart_with_items(db, cart.id)  # Returning the updated basket


@router.delete("/", response_model=Cart)
async def clear(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    cart = await get_or_create_cart(db, current_user.id)
    await clear_cart(db, cart.id)
    return await get_cart_with_items(db, cart.id)  # Returning the emptied basket
