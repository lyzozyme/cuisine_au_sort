"""Liste de courses d'un planning : agrégation des quantités par ingrédient et par unité.

Grâce aux unités normalisées (g, ml, pièce…), les quantités d'un même ingrédient s'additionnent
directement. Un ingrédient utilisé dans des unités différentes (ex. 200 g et 2 tbsp de farine)
apparaît sur une ligne par unité : aucune conversion poids/volume n'est tentée.
"""

import itertools
import uuid

from sqlalchemy import Numeric, func, literal, select
from sqlalchemy.orm import Session

from app.models import Aisle, Ingredient, PlanEntry, Recipe, RecipeIngredient, User
from app.models.enums import enum_order
from app.schemas.shopping_list import (
    ShoppingAisleRead,
    ShoppingIngredientRead,
    ShoppingItemRead,
    ShoppingListRead,
)
from app.services.plans import get_plan

# Ordre des rayons : celui de l'énumération (parcours type d'un magasin), pas l'ordre alphabétique
_AISLE_ORDER = enum_order(Aisle, Ingredient.aisle)
# Précision des colonnes de quantité : NUMERIC(10, 3)
_QUANTITY_SCALE = 3


def build_shopping_list(
    db: Session, user: User, plan_id: uuid.UUID, *, servings: int | None = None
) -> ShoppingListRead:
    """Liste de courses du planning.

    Sans `servings`, les quantités des recettes sont prises telles quelles. Avec `servings`,
    chaque recette est ramenée à ce nombre de personnes (quantité × servings / recipe.servings).
    Une recette planifiée plusieurs fois compte autant de fois.
    """
    plan = get_plan(db, user, plan_id, with_entries=False)

    quantity = RecipeIngredient.quantity
    if servings is not None:
        quantity = quantity * literal(servings, Numeric) / Recipe.servings
    total = func.round(func.sum(quantity), _QUANTITY_SCALE)

    rows = db.execute(
        select(Ingredient.aisle, Ingredient.id, Ingredient.name, RecipeIngredient.unit, total)
        .select_from(PlanEntry)
        .join(Recipe, Recipe.id == PlanEntry.recipe_id)
        .join(RecipeIngredient, RecipeIngredient.recipe_id == Recipe.id)
        .join(Ingredient, Ingredient.id == RecipeIngredient.ingredient_id)
        .where(PlanEntry.plan_id == plan.id)
        .group_by(Ingredient.id, Ingredient.name, Ingredient.aisle, RecipeIngredient.unit)
        .order_by(_AISLE_ORDER, func.lower(Ingredient.name), Ingredient.id, RecipeIngredient.unit)
    ).all()

    aisles = [
        ShoppingAisleRead(
            aisle=aisle,
            items=[
                ShoppingItemRead(
                    ingredient=ShoppingIngredientRead(id=ingredient_id, name=name),
                    quantity=quantity,
                    unit=unit,
                )
                for _, ingredient_id, name, unit, quantity in items
            ],
        )
        for aisle, items in itertools.groupby(rows, key=lambda row: row.aisle)
    ]
    return ShoppingListRead(
        plan_id=plan.id, week_start=plan.week_start, servings=servings, aisles=aisles
    )
