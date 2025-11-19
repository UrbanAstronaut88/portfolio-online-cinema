from sqlalchemy.orm import Session
from app.models.orders import Order, OrderItem, OrderStatusEnum
from app.schemas.orders import OrderCreate
from app.crud.cart import get_or_create_cart  # для переноса из корзины
from app.models.cart import CartItem


def create_order_from_cart(db: Session, user_id: int):
    cart = get_or_create_cart(db, user_id)
    if not cart.items:
        return None  # пустая корзина

    total = sum(item.movie.price for item in cart.items)  # рассчитать сумму
    db_order = Order(user_id=user_id, total_amount=total)
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    for cart_item in cart.items:
        db_item = OrderItem(order_id=db_order.id, movie_id=cart_item.movie_id, price_at_order=cart_item.movie.price)
        db.add(db_item)
    db.commit()

    # Очистить корзину
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()

    return db_order


def get_orders(db: Session, user_id: int = None, skip: int = 0, limit: int = 10):
    query = db.query(Order)
    if user_id:
        query = query.filter(Order.user_id == user_id)
    return query.offset(skip).limit(limit).all()


def cancel_order(db: Session, order_id: int):
    order = db.query(Order).filter(Order.id == order_id).first()
    if order and order.status == OrderStatusEnum.PENDING:
        order.status = OrderStatusEnum.CANCELED
        db.commit()
        db.refresh(order)
        return order
    return None

# позже добавить update_status (для оплаты), filters для модераторов