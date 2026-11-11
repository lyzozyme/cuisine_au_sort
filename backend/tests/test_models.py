from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.seed import seed_default_user
from app.models import (
    Aisle,
    Ingredient,
    Meal,
    PlanEntry,
    Recipe,
    RecipeIngredient,
    Unit,
    User,
    Visibility,
    WeeklyPlan,
)


def make_user(session: Session, email: str = "alice@example.com") -> User:
    user = User(email=email, display_name=email.split("@")[0])
    session.add(user)
    session.flush()
    return user


def make_ingredient(session: Session, name: str = "Farine") -> Ingredient:
    ingredient = Ingredient(name=name, default_unit=Unit.GRAM, aisle=Aisle.GROCERY)
    session.add(ingredient)
    session.flush()
    return ingredient


def make_recipe(session: Session, owner: User, name: str = "Crêpes", **kwargs) -> Recipe:
    recipe = Recipe(owner=owner, name=name, **kwargs)
    session.add(recipe)
    session.flush()
    return recipe


def test_recipe_with_ingredients_and_defaults(db_session: Session) -> None:
    owner = make_user(db_session)
    flour = make_ingredient(db_session)
    recipe = make_recipe(db_session, owner, servings=4)
    recipe.ingredients.append(
        RecipeIngredient(ingredient=flour, quantity=Decimal("250"), unit=Unit.GRAM)
    )
    db_session.flush()
    db_session.expire_all()

    loaded = db_session.get(Recipe, recipe.id)
    assert loaded is not None
    assert loaded.visibility is Visibility.PRIVATE
    assert loaded.tags == []
    assert loaded.instructions == ""
    assert loaded.created_at is not None and loaded.updated_at is not None
    assert [(ri.ingredient.name, ri.quantity, ri.unit) for ri in loaded.ingredients] == [
        ("Farine", Decimal("250.000"), Unit.GRAM)
    ]


def test_enum_values_are_stored_as_lowercase_strings(db_session: Session) -> None:
    make_ingredient(db_session)
    stored = db_session.execute(text("SELECT default_unit, aisle FROM ingredients")).one()
    assert tuple(stored) == ("g", "grocery")


def test_recipe_name_is_unique_per_owner(db_session: Session) -> None:
    alice = make_user(db_session, "alice@example.com")
    bob = make_user(db_session, "bob@example.com")
    make_recipe(db_session, alice, "Ratatouille")
    make_recipe(db_session, bob, "Ratatouille")  # même nom, autre propriétaire : autorisé

    with pytest.raises(IntegrityError, match="uq_recipes_owner_id_name"):
        make_recipe(db_session, alice, "Ratatouille")


@pytest.mark.parametrize(
    ("sql", "constraint"),
    [
        (
            "INSERT INTO ingredients (id, name, default_unit, aisle) "
            "VALUES (gen_random_uuid(), 'Sel', 'kg', 'spices')",
            "ck_ingredients_unit",
        ),
        (
            "INSERT INTO ingredients (id, name, default_unit, aisle) "
            "VALUES (gen_random_uuid(), 'Sel', 'g', 'inconnu')",
            "ck_ingredients_aisle",
        ),
    ],
)
def test_enum_check_constraints(db_session: Session, sql: str, constraint: str) -> None:
    with pytest.raises(IntegrityError, match=constraint):
        db_session.execute(text(sql))


def test_quantity_must_be_positive(db_session: Session) -> None:
    recipe = make_recipe(db_session, make_user(db_session))
    recipe.ingredients.append(
        RecipeIngredient(ingredient=make_ingredient(db_session), quantity=0, unit=Unit.GRAM)
    )
    with pytest.raises(IntegrityError, match="ck_recipe_ingredients_quantity_positive"):
        db_session.flush()


def test_deleting_recipe_cascades_ingredients_and_detaches_forks(db_session: Session) -> None:
    owner = make_user(db_session)
    recipe = make_recipe(db_session, owner)
    recipe.ingredients.append(
        RecipeIngredient(ingredient=make_ingredient(db_session), quantity=1, unit=Unit.GRAM)
    )
    fork = make_recipe(db_session, owner, "Crêpes (copie)", source_recipe=recipe)

    db_session.delete(recipe)
    db_session.flush()
    db_session.expire_all()

    assert db_session.scalar(select(func.count()).select_from(RecipeIngredient)) == 0
    assert db_session.get(Recipe, fork.id).source_recipe_id is None


def test_planned_recipe_cannot_be_deleted(db_session: Session) -> None:
    owner = make_user(db_session)
    recipe = make_recipe(db_session, owner)
    plan = WeeklyPlan(owner=owner, week_start=date(2026, 11, 9))
    plan.entries.append(PlanEntry(day=0, meal=Meal.DINNER, recipe=recipe))
    db_session.add(plan)
    db_session.flush()

    with pytest.raises(IntegrityError, match="fk_plan_entries_recipe_id_recipes"):
        db_session.execute(text("DELETE FROM recipes WHERE id = :id"), {"id": recipe.id})


def test_ingredient_in_use_cannot_be_deleted(db_session: Session) -> None:
    flour = make_ingredient(db_session)
    recipe = make_recipe(db_session, make_user(db_session))
    recipe.ingredients.append(RecipeIngredient(ingredient=flour, quantity=1, unit=Unit.GRAM))
    db_session.flush()

    with pytest.raises(IntegrityError, match="fk_recipe_ingredients_ingredient_id_ingredients"):
        db_session.execute(text("DELETE FROM ingredients WHERE id = :id"), {"id": flour.id})


@pytest.mark.parametrize(
    ("slots", "constraint"),
    [
        ([(7, Meal.LUNCH)], "ck_plan_entries_day_of_week"),
        ([(1, Meal.LUNCH), (1, Meal.LUNCH)], "uq_plan_entries_plan_id_day_meal"),
    ],
)
def test_plan_entry_slot_is_unique_and_day_bounded(
    db_session: Session, slots: list[tuple[int, Meal]], constraint: str
) -> None:
    owner = make_user(db_session)
    recipe = make_recipe(db_session, owner)
    plan = WeeklyPlan(owner=owner, week_start=date(2026, 11, 9))
    plan.entries += [PlanEntry(day=day, meal=meal, recipe=recipe) for day, meal in slots]
    db_session.add(plan)

    with pytest.raises(IntegrityError, match=constraint):
        db_session.flush()


def test_tags_can_be_filtered_with_array_overlap(db_session: Session) -> None:
    owner = make_user(db_session)
    make_recipe(db_session, owner, "Salade", tags=["végétarien", "rapide"])
    make_recipe(db_session, owner, "Bœuf bourguignon", tags=["viande", "long"])
    make_recipe(db_session, owner, "Omelette")

    excluded = ["viande"]
    names = db_session.scalars(
        select(Recipe.name).where(~Recipe.tags.overlap(excluded)).order_by(Recipe.name)
    ).all()
    assert names == ["Omelette", "Salade"]


def test_seed_default_user_is_idempotent(db_session: Session) -> None:
    first = seed_default_user(db_session)
    second = seed_default_user(db_session)

    assert first.id == second.id
    assert db_session.scalar(select(func.count()).select_from(User)) == 1


def test_plan_entries_are_ordered_lunch_before_dinner(db_session: Session) -> None:
    owner = make_user(db_session)
    recipe = make_recipe(db_session, owner)
    plan = WeeklyPlan(owner=owner, week_start=date(2026, 11, 9))
    plan.entries += [
        PlanEntry(day=1, meal=Meal.DINNER, recipe=recipe),
        PlanEntry(day=0, meal=Meal.DINNER, recipe=recipe),
        PlanEntry(day=0, meal=Meal.LUNCH, recipe=recipe),
    ]
    db_session.add(plan)
    db_session.flush()
    db_session.expire_all()

    loaded = db_session.get(WeeklyPlan, plan.id)
    assert [(e.day, e.meal) for e in loaded.entries] == [
        (0, Meal.LUNCH),
        (0, Meal.DINNER),
        (1, Meal.DINNER),
    ]


def test_in_place_tag_changes_are_persisted(db_session: Session) -> None:
    recipe = make_recipe(db_session, make_user(db_session), tags=["rapide"])
    recipe.tags.append("végétarien")
    db_session.flush()
    db_session.expire_all()

    assert db_session.get(Recipe, recipe.id).tags == ["rapide", "végétarien"]


def test_deleting_user_with_loaded_recipes_cascades(db_session: Session) -> None:
    owner = make_user(db_session)
    make_recipe(db_session, owner)
    assert len(owner.recipes) == 1  # collection chargée

    db_session.delete(owner)
    db_session.flush()

    assert db_session.scalar(select(func.count()).select_from(Recipe)) == 0
