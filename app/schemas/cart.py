from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime


class CartItemBase(BaseModel):
    movie_id: int


class CartItemCreate(CartItemBase):
    pass


class CartItem(CartItemBase):
    id: int
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartBase(BaseModel):
    user_id: int


class Cart(CartBase):
    id: int
    items: List[CartItem] = []

    model_config = ConfigDict(from_attributes=True)
