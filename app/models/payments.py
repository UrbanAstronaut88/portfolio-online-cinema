from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SQLEnum, Float, String
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base


class PaymentStatusEnum(str, Enum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(SQLEnum(PaymentStatusEnum), default=PaymentStatusEnum.SUCCESSFUL ,nullable=False)
    amount = Column(Float, nullable=False)
    external_payment_id = Column(String, nullable=True)   # Stripe charge_id

    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    items = relationship("PaymentItem", back_populates="payment")


class PaymentItem(Base):
    __tablename__ = "payment_items"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=False)
    price_at_payment = Column(Float, nullable=False)

    payment = relationship("Payment", back_populates="items")
    order_item = relationship("OrderItem")
