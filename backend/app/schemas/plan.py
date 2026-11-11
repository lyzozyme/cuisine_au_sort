import datetime as dt
import uuid
from typing import Annotated, Self

from pydantic import Field, field_validator, model_validator

from app.models.enums import Meal
from app.schemas.common import InputModel, ReadModel
from app.schemas.recipe import Tag

DAYS_PER_WEEK = 7


def upcoming_monday(today: dt.date | None = None) -> dt.date:
    """Lundi de la semaine à venir (aujourd'hui si on est lundi)."""
    today = today or dt.date.today()
    return today + dt.timedelta(days=-today.weekday() % DAYS_PER_WEEK)


class DrawRequest(InputModel):
    """Paramètres du tirage au sort d'une semaine de repas.

    Les repas sont placés dans l'ordre chronologique : avec `meals=["dinner"]` et
    `meal_count=5`, on obtient les dîners du lundi au vendredi.
    """

    week_start: dt.date = Field(
        default_factory=upcoming_monday,
        description="Lundi de la semaine planifiée (par défaut : le prochain lundi)",
    )
    meal_count: Annotated[int, Field(ge=1, le=DAYS_PER_WEEK * len(Meal))] = DAYS_PER_WEEK
    meals: Annotated[list[Meal], Field(min_length=1, description="Repas à planifier par jour")] = [
        Meal.DINNER
    ]
    exclude_tags: Annotated[list[Tag], Field(max_length=20)] = []
    mine_only: bool = Field(
        default=False, description="Ne tirer que parmi mes recettes (sinon : toutes les visibles)"
    )

    @field_validator("week_start")
    @classmethod
    def _must_be_monday(cls, value: dt.date) -> dt.date:
        if value.weekday() != 0:
            raise ValueError("week_start doit être un lundi")
        return value

    @field_validator("meals")
    @classmethod
    def _unique_and_chronological(cls, value: list[Meal]) -> list[Meal]:
        if len(set(value)) != len(value):
            raise ValueError("chaque repas ne peut être indiqué qu'une fois")
        order = list(Meal)
        return sorted(value, key=order.index)

    @model_validator(mode="after")
    def _enough_slots(self) -> Self:
        slots = DAYS_PER_WEEK * len(self.meals)
        if self.meal_count > slots:
            raise ValueError(f"meal_count dépasse le nombre de créneaux de la semaine ({slots})")
        return self


class PlanRecipeRead(ReadModel):
    id: uuid.UUID
    name: str
    servings: int
    tags: list[str]


class PlanEntryRead(ReadModel):
    id: uuid.UUID
    day: int = Field(description="0 = lundi … 6 = dimanche")
    date: dt.date = Field(validation_alias="scheduled_on")
    meal: Meal
    recipe: PlanRecipeRead


class PlanRead(ReadModel):
    id: uuid.UUID
    week_start: dt.date
    entries: list[PlanEntryRead]
    created_at: dt.datetime
    updated_at: dt.datetime
