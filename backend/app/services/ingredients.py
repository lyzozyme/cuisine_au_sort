"""Catalogue global d'ingrédients.

Pour l'instant tout utilisateur peut le modifier (un seul utilisateur). Avec le multi-utilisateur,
il faudra restreindre la modification aux ingrédients personnels (`created_by`).
"""

import uuid
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Aisle, Ingredient, RecipeIngredient
from app.schemas.ingredient import IngredientCreate, IngredientUpdate
from app.services.common import commit_or_conflict, contains_ignore_case
from app.services.errors import ConflictError, NotFoundError


def list_ingredients(
    db: Session,
    *,
    search: str | None = None,
    aisle: Aisle | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Ingredient]:
    query = select(Ingredient).order_by(func.lower(Ingredient.name)).limit(limit).offset(offset)
    if search:
        query = query.where(contains_ignore_case(Ingredient.name, search))
    if aisle is not None:
        query = query.where(Ingredient.aisle == aisle)
    return db.scalars(query).all()


def get_ingredient(db: Session, ingredient_id: uuid.UUID) -> Ingredient:
    ingredient = db.get(Ingredient, ingredient_id)
    if ingredient is None:
        raise NotFoundError("Ingrédient introuvable")
    return ingredient


def _ensure_name_available(db: Session, name: str, exclude_id: uuid.UUID | None = None) -> None:
    # Insensible à la casse : « Farine » et « farine » seraient comptés à part dans la liste de
    # courses. (La contrainte en base reste sensible à la casse.)
    query = select(Ingredient.id).where(func.lower(Ingredient.name) == name.lower())
    if exclude_id is not None:
        query = query.where(Ingredient.id != exclude_id)
    if db.scalars(query).first() is not None:
        raise ConflictError(f"L'ingrédient « {name} » existe déjà")


def create_ingredient(db: Session, data: IngredientCreate) -> Ingredient:
    _ensure_name_available(db, data.name)
    ingredient = Ingredient(**data.model_dump())
    db.add(ingredient)
    commit_or_conflict(db, f"L'ingrédient « {data.name} » existe déjà")
    return ingredient


def update_ingredient(db: Session, ingredient_id: uuid.UUID, data: IngredientUpdate) -> Ingredient:
    ingredient = get_ingredient(db, ingredient_id)
    if data.name is not None:
        _ensure_name_available(db, data.name, exclude_id=ingredient.id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(ingredient, field, value)
    commit_or_conflict(db, f"L'ingrédient « {ingredient.name} » existe déjà")
    return ingredient


def delete_ingredient(db: Session, ingredient_id: uuid.UUID) -> None:
    ingredient = get_ingredient(db, ingredient_id)
    usage = db.scalar(select(func.count()).where(RecipeIngredient.ingredient_id == ingredient.id))
    if usage:
        raise ConflictError(f"Ingrédient utilisé dans {usage} recette(s) : suppression impossible")
    db.delete(ingredient)
    commit_or_conflict(db, "Ingrédient utilisé dans une recette : suppression impossible")
