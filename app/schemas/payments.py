from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PaymentStatusEnum(str, Enum):
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class PaymentItemBase(BaseModel):
    order_item_id: int
    price_at_payment: float


class PaymentItem(PaymentItemBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class PaymentBase(BaseModel):
    status: PaymentStatusEnum
    amount: float
    external_payment_id: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class Payment(PaymentBase):
    id: int
    created_at: datetime
    user_id: int
    order_id: int
    items: List[PaymentItem] = []

    model_config = ConfigDict(from_attributes=True)
