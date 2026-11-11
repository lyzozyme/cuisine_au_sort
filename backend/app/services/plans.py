"""Plannings hebdomadaires : tirage au sort, consultation, suppression.

Un planning est toujours privé : seul son propriétaire y a accès (les autres reçoivent 404).
"""

import random
import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import PlanEntry, Recipe, User, WeeklyPlan
from app.schemas.plan import DAYS_PER_WEEK, DrawRequest
from app.services.common import commit_or_conflict
from app.services.errors import InvalidInputError, NotFoundError
from app.services.recipes import recipe_pool_condition

_RECIPE_FK = "fk_plan_entries_recipe_id_recipes"


def _owned_plans(user: User, *, with_entries: bool = True):
    query = select(WeeklyPlan).where(WeeklyPlan.owner_id == user.id)
    if with_entries:
        query = query.options(selectinload(WeeklyPlan.entries).joinedload(PlanEntry.recipe))
    return query


def list_plans(
    db: Session, user: User, *, limit: int = 20, offset: int = 0
) -> Sequence[WeeklyPlan]:
    query = (
        _owned_plans(user)
        .order_by(WeeklyPlan.week_start.desc(), WeeklyPlan.created_at.desc(), WeeklyPlan.id)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(query).all()


def get_plan(
    db: Session, user: User, plan_id: uuid.UUID, *, with_entries: bool = True
) -> WeeklyPlan:
    """Planning de l'utilisateur. `with_entries=False` : sans charger les entrées ni les recettes
    (vérification d'accès seule)."""
    query = _owned_plans(user, with_entries=with_entries).where(WeeklyPlan.id == plan_id)
    plan = db.scalars(query).one_or_none()
    if plan is None:
        raise NotFoundError("Planning introuvable")
    return plan


def delete_plan(db: Session, user: User, plan_id: uuid.UUID) -> None:
    # Entrées non chargées : supprimées par le ON DELETE CASCADE de la base (passive_deletes)
    db.delete(get_plan(db, user, plan_id, with_entries=False))
    db.commit()


def _drawable_recipe_ids(db: Session, user: User, request: DrawRequest) -> list[uuid.UUID]:
    query = (
        select(Recipe.id)
        .where(recipe_pool_condition(user, mine_only=request.mine_only))
        .order_by(Recipe.id)  # ordre stable : tirage reproductible avec rng
    )
    if request.exclude_tags:
        query = query.where(~Recipe.tags.overlap(request.exclude_tags))
    return list(db.scalars(query))


def draw_plan(
    db: Session, user: User, request: DrawRequest, *, rng: random.Random | None = None
) -> WeeklyPlan:
    """Tire `meal_count` recettes distinctes et les répartit chronologiquement sur la semaine.

    `rng` permet de rendre le tirage déterministe (tests).
    """
    slots = [(day, meal) for day in range(DAYS_PER_WEEK) for meal in request.meals]
    slots = slots[: request.meal_count]

    candidates = _drawable_recipe_ids(db, user, request)
    if len(candidates) < len(slots):
        raise InvalidInputError(
            f"Pas assez de recettes pour un tirage sans doublon : {len(candidates)} "
            f"disponible(s) pour {len(slots)} repas"
        )
    drawn = (rng or random).sample(candidates, k=len(slots))

    plan = WeeklyPlan(
        owner=user,
        week_start=request.week_start,
        entries=[
            PlanEntry(day=day, meal=meal, recipe_id=recipe_id)
            for (day, meal), recipe_id in zip(slots, drawn, strict=True)
        ],
    )
    db.add(plan)
    commit_or_conflict(
        db,
        "Une recette tirée vient d'être supprimée : relancez le tirage",
        constraint=_RECIPE_FK,
    )
    return get_plan(db, user, plan.id)
