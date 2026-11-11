import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import Field, StringConstraints, field_validator

from app.models.enums import Aisle, Unit, Visibility
from app.schemas.common import DecimalNumber, InputModel, PatchModel, ReadModel
from app.services.units import InputUnit

RecipeName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
# Tags normalisés en minuscules : l'exclusion de tags au tirage au sort est une comparaison exacte
Tag = Annotated[
    str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=1, max_length=50)
]
Servings = Annotated[int, Field(ge=1, le=100)]
Description = Annotated[str, Field(max_length=5_000)]
Instructions = Annotated[str, Field(max_length=20_000)]
# Borne haute choisie pour que la valeur convertie (ex. 9999 kg -> 9 999 000 g) tienne
# dans la colonne NUMERIC(10, 3)
Quantity = Annotated[Decimal, Field(gt=0, le=9999, decimal_places=3)]


class RecipeIngredientIn(InputModel):
    ingredient_id: uuid.UUID
    quantity: Quantity
    unit: InputUnit | None = Field(
        default=None, description="Unité saisie ; par défaut, l'unité par défaut de l'ingrédient"
    )


def _dedupe_tags(tags: list[str] | None) -> list[str] | None:
    return None if tags is None else sorted(set(tags))


def _check_unique_ingredients(
    items: list[RecipeIngredientIn] | None,
) -> list[RecipeIngredientIn] | None:
    if items is not None:
        ids = [item.ingredient_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("un même ingrédient ne peut apparaître qu'une fois par recette")
    return items


class RecipeCreate(InputModel):
    name: RecipeName
    description: Description | None = None
    servings: Servings = 2
    instructions: Instructions = ""
    tags: Annotated[list[Tag], Field(max_length=20)] = []
    visibility: Visibility = Visibility.PRIVATE
    ingredients: Annotated[list[RecipeIngredientIn], Field(max_length=100)] = []

    normalize_tags = field_validator("tags")(_dedupe_tags)
    check_unique_ingredients = field_validator("ingredients")(_check_unique_ingredients)


class RecipeUpdate(PatchModel):
    """Mise à jour partielle. Si `ingredients` est fourni, il remplace la liste complète."""

    nullable_fields = frozenset({"description"})

    name: RecipeName | None = None
    description: Description | None = None
    servings: Servings | None = None
    instructions: Instructions | None = None
    tags: Annotated[list[Tag], Field(max_length=20)] | None = None
    visibility: Visibility | None = None
    ingredients: Annotated[list[RecipeIngredientIn], Field(max_length=100)] | None = None

    normalize_tags = field_validator("tags")(_dedupe_tags)
    check_unique_ingredients = field_validator("ingredients")(_check_unique_ingredients)


class IngredientSummary(ReadModel):
    id: uuid.UUID
    name: str
    aisle: Aisle


class RecipeIngredientRead(ReadModel):
    ingredient: IngredientSummary
    quantity: DecimalNumber
    unit: Unit


class RecipeRead(ReadModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: str | None
    servings: int
    instructions: str
    tags: list[str]
    visibility: Visibility
    source_recipe_id: uuid.UUID | None
    ingredients: list[RecipeIngredientRead]
    created_at: datetime
    updated_at: datetime

    @field_validator("ingredients")
    @classmethod
    def _sort_ingredients(cls, items: list[RecipeIngredientRead]) -> list[RecipeIngredientRead]:
        # Pas d'ordre stocké en base : ordre alphabétique pour une réponse stable
        return sorted(items, key=lambda item: item.ingredient.name.lower())
