"""Modèles SQLAlchemy. Tous importés ici pour enregistrer les tables dans `Base.metadata`
(utilisé par Alembic)."""

from app.models.enums import Aisle, Meal, Unit, Visibility
from app.models.ingredient import Ingredient
from app.models.plan import PlanEntry, WeeklyPlan
from app.models.recipe import Recipe, RecipeIngredient
from app.models.user import User

__all__ = [
    "Aisle",
    "Ingredient",
    "Meal",
    "PlanEntry",
    "Recipe",
    "RecipeIngredient",
    "Unit",
    "User",
    "Visibility",
    "WeeklyPlan",
]
