import datetime as dt
import uuid

from pydantic import BaseModel

from app.models.enums import Aisle, Unit
from app.schemas.common import DecimalNumber


class ShoppingIngredientRead(BaseModel):
    id: uuid.UUID
    name: str


class ShoppingItemRead(BaseModel):
    ingredient: ShoppingIngredientRead
    quantity: DecimalNumber
    unit: Unit


class ShoppingAisleRead(BaseModel):
    aisle: Aisle
    items: list[ShoppingItemRead]


class ShoppingListRead(BaseModel):
    plan_id: uuid.UUID
    week_start: dt.date
    servings: int | None
    aisles: list[ShoppingAisleRead]
