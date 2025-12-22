from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


class OrderStatusEnum(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"


class OrderItemBase(BaseModel):
    movie_id: int
    price_at_order: float


class OrderItem(OrderItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    status: OrderStatusEnum
    total_amount: Optional[float] = None


class OrderCreate(OrderBase):
    pass


class Order(OrderBase):
    id: int
    created_at: datetime
    user_id: int
    items: List[OrderItem] = []

    model_config = ConfigDict(from_attributes=True)
