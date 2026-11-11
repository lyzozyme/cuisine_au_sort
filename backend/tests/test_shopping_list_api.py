import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Meal, PlanEntry, User, WeeklyPlan
from tests.factories import MONDAY, create_ingredient, create_recipe, draw


def line(ingredient: dict, quantity: float, unit: str | None = None) -> dict:
    payload = {"ingredient_id": ingredient["id"], "quantity": quantity}
    return payload | ({"unit": unit} if unit else {})


@pytest.fixture
def plan(client: TestClient) -> dict:
    """Planning des 3 recettes ci-dessous (toutes tirées : 3 repas pour 3 recettes)."""
    flour = create_ingredient(client, "Farine", "g", "grocery")
    milk = create_ingredient(client, "Lait", "ml", "dairy")
    eggs = create_ingredient(client, "Œufs", "piece", "dairy")
    tomato = create_ingredient(client, "Tomate", "piece", "produce")
    salt = create_ingredient(client, "Sel", "g", "spices")

    create_recipe(
        client,
        "Crêpes",
        servings=4,
        ingredients=[
            line(flour, 250),
            line(milk, 500),
            line(eggs, 4),
            line(salt, 1, "pinch"),
        ],
    )
    create_recipe(
        client,
        "Gâteau",
        servings=8,
        ingredients=[line(flour, 200), line(eggs, 3), line(milk, 0.1, "l")],
    )
    create_recipe(client, "Salade", servings=2, ingredients=[line(tomato, 3), line(salt, 2)])
    return draw(client, meal_count=3)


def summary(shopping_list: dict) -> list[tuple[str, list[tuple[str, float, str]]]]:
    return [
        (
            aisle["aisle"],
            [(i["ingredient"]["name"], i["quantity"], i["unit"]) for i in aisle["items"]],
        )
        for aisle in shopping_list["aisles"]
    ]


def test_shopping_list_aggregates_by_ingredient_and_unit(client: TestClient, plan: dict) -> None:
    response = client.get(f"/plans/{plan['id']}/shopping-list")

    assert response.status_code == 200
    body = response.json()
    assert (body["plan_id"], body["week_start"], body["servings"]) == (plan["id"], MONDAY, None)
    # Rayons dans l'ordre du magasin ; une ligne par (ingrédient, unité)
    assert summary(body) == [
        ("produce", [("Tomate", 3, "piece")]),
        ("dairy", [("Lait", 600, "ml"), ("Œufs", 7, "piece")]),
        ("grocery", [("Farine", 450, "g")]),
        ("spices", [("Sel", 2, "g"), ("Sel", 1, "pinch")]),
    ]


def test_shopping_list_scales_to_servings(client: TestClient, plan: dict) -> None:
    body = client.get(f"/plans/{plan['id']}/shopping-list", params={"servings": 2}).json()

    # Crêpes ×2/4, Gâteau ×2/8, Salade ×2/2
    assert body["servings"] == 2
    assert summary(body) == [
        ("produce", [("Tomate", 3, "piece")]),
        ("dairy", [("Lait", 275, "ml"), ("Œufs", 2.75, "piece")]),
        ("grocery", [("Farine", 175, "g")]),
        ("spices", [("Sel", 2, "g"), ("Sel", 0.5, "pinch")]),
    ]


def test_scaled_quantities_are_rounded(client: TestClient) -> None:
    eggs = create_ingredient(client, "Œufs", "piece", "dairy")
    create_recipe(client, "Omelette", servings=3, ingredients=[line(eggs, 1)])
    plan = draw(client, meal_count=1)

    body = client.get(f"/plans/{plan['id']}/shopping-list", params={"servings": 2}).json()

    assert summary(body) == [("dairy", [("Œufs", 0.667, "piece")])]


def test_recipe_planned_twice_counts_twice(
    client: TestClient, db_session: Session, default_user: User
) -> None:
    rice = create_ingredient(client, "Riz", "g")
    recipe = create_recipe(client, "Riz", ingredients=[line(rice, 150)])
    plan = WeeklyPlan(owner=default_user, week_start=date(2026, 11, 9))
    recipe_id = uuid.UUID(recipe["id"])
    plan.entries += [
        PlanEntry(day=0, meal=Meal.DINNER, recipe_id=recipe_id),
        PlanEntry(day=1, meal=Meal.DINNER, recipe_id=recipe_id),
    ]
    db_session.add(plan)
    db_session.flush()

    body = client.get(f"/plans/{plan.id}/shopping-list").json()

    assert summary(body) == [("grocery", [("Riz", 300, "g")])]


def test_shopping_list_of_recipes_without_ingredients_is_empty(client: TestClient) -> None:
    create_recipe(client, "Restes")
    plan = draw(client, meal_count=1)

    assert client.get(f"/plans/{plan['id']}/shopping-list").json()["aisles"] == []


@pytest.mark.parametrize("servings", [0, 101, "deux"])
def test_invalid_servings(client: TestClient, plan: dict, servings) -> None:
    response = client.get(f"/plans/{plan['id']}/shopping-list", params={"servings": servings})
    assert response.status_code == 422
