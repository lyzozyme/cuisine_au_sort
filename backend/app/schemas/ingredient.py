import uuid
from datetime import datetime
from typing import Annotated

from pydantic import StringConstraints

from app.models.enums import Aisle, Unit
from app.schemas.common import InputModel, PatchModel, ReadModel

IngredientName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]


class IngredientCreate(InputModel):
    name: IngredientName
    default_unit: Unit
    aisle: Aisle = Aisle.OTHER


class IngredientUpdate(PatchModel):
    name: IngredientName | None = None
    default_unit: Unit | None = None
    aisle: Aisle | None = None


class IngredientRead(ReadModel):
    id: uuid.UUID
    name: str
    default_unit: Unit
    aisle: Aisle
    created_at: datetime
    updated_at: datetime
