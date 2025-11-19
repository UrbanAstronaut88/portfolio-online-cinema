from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(OrderStatusEnum), default=OrderStatusEnum.PENDING, nullable=False)
    total_amount = Column(Float, nullable=True)

    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    movie_id = Column(Integer, ForeignKey("movies.id"), nullable=False)
    price_at_order = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    movie = relationship("Movie")