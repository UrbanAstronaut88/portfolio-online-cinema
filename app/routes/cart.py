from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.cart import Cart, CartItemCreate
from app.crud.cart import get_or_create_cart, add_item_to_cart, remove_item_from_cart, clear_cart
# Добавить current_user от auth


router = APIRouter(prefix="/cart", tags=["cart"])

@router.get("/", response_model=Cart)
def get_cart(db: Session = Depends(get_db)):  # user_id от current_user
    # exmpl: user_id = 1 (замени на auth)
    cart = get_or_create_cart(db, user_id=1)
    return cart

@router.post("/items", response_model=Cart)
def add_item(item: CartItemCreate, db: Session = Depends(get_db)):
    # user_id = current_user.id
    cart = get_or_create_cart(db, user_id=1)
    added = add_item_to_cart(db, cart.id, item)
    if not added:
        raise HTTPException(400, "Item already in cart or purchased")
    return cart

@router.delete("/items/{item_id}", response_model=Cart)
def remove_item(item_id: int, db: Session = Depends(get_db)):
    # Проверка ownership
    removed = remove_item_from_cart(db, item_id)
    if not removed:
        raise HTTPException(404, "Item not found")
    # вернуть обновлённую корзину

@router.delete("/", response_model=Cart)
def clear(db: Session = Depends(get_db)):
    # user_id = current_user.id
    cart = get_or_create_cart(db, user_id=1)
    clear_cart(db, cart.id)
    return cart
