from sqlalchemy.orm import Session
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemCreate
from app.models.movies import Movie

def get_or_create_cart(db: Session, user_id: int):
    cart = db.query(Cart).filter(Cart.user_id == user_id).first()
    if not cart:
        cart = Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def add_item_to_cart(db: Session, cart_id: int, item: CartItemCreate):
    # проверить, не куплен ли фильм (позже с orders)
    existing = db.query(CartItem).filter(CartItem.cart_id == cart_id, CartItem.movie_id == item.movie_id).first()
    if existing:
        return None  # уже в корзине
    db_item = CartItem(cart_id=cart_id, movie_id=item.movie_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def remove_item_from_cart(db: Session, item_id: int):
    item = db.query(CartItem).filter(CartItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return item

def clear_cart(db: Session, cart_id: int):
    db.query(CartItem).filter(CartItem.cart_id == cart_id).delete()
    db.commit()

# добавить get_cart с items (joinedload для movie details)
