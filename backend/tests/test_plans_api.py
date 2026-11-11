import random
import uuid
from collections import Counter
from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Recipe, User
from app.schemas.plan import DrawRequest, upcoming_monday
from app.services.plans import draw_plan
from tests.factories import MONDAY, create_recipe, draw


@pytest.fixture
def seven_recipes(client: TestClient) -> list[dict]:
    return [create_recipe(client, f"Recette {i}") for i in range(7)]


def slots(plan: dict) -> list[tuple[int, str, str]]:
    return [(e["day"], e["date"], e["meal"]) for e in plan["entries"]]


# --- Tirage --------------------------------------------------------------------------------------


def test_draw_default_week_of_dinners(client: TestClient, seven_recipes: list[dict]) -> None:
    plan = draw(client)

    assert plan["week_start"] == MONDAY
    assert slots(plan) == [(d, f"2026-11-{9 + d:02d}", "dinner") for d in range(7)]
    drawn = [e["recipe"]["id"] for e in plan["entries"]]
    assert sorted(drawn) == sorted(r["id"] for r in seven_recipes)  # 7 recettes, sans doublon


def test_draw_fills_slots_chronologically(client: TestClient, seven_recipes: list[dict]) -> None:
    plan = draw(client, meal_count=5, meals=["dinner", "lunch"])

    assert [(e["day"], e["meal"]) for e in plan["entries"]] == [
        (0, "lunch"),
        (0, "dinner"),
        (1, "lunch"),
        (1, "dinner"),
        (2, "lunch"),
    ]
    assert len({e["recipe"]["id"] for e in plan["entries"]}) == 5


def test_draw_excludes_tags(client: TestClient) -> None:
    create_recipe(client, "Steak", tags=["viande"])
    create_recipe(client, "Gratin", tags=["long", "végétarien"])
    create_recipe(client, "Omelette", tags=["rapide"])
    create_recipe(client, "Salade")

    plan = draw(client, meal_count=2, exclude_tags=["VIANDE", " long "])

    assert {e["recipe"]["name"] for e in plan["entries"]} == {"Omelette", "Salade"}


def test_draw_fails_without_enough_recipes(client: TestClient) -> None:
    create_recipe(client, "Seule")

    response = client.post("/plans/draw", json={"week_start": MONDAY, "meal_count": 2})

    assert response.status_code == 422
    assert "1 disponible(s) pour 2 repas" in response.json()["detail"]
    assert client.get("/plans").json() == []


def test_draw_pool_respects_visibility(
    client: TestClient,
    default_user: User,
    other_user: User,
    act_as: Callable[[User], None],
) -> None:
    create_recipe(client, "Ma recette")
    act_as(other_user)
    create_recipe(client, "Publique de Bob", visibility="public")
    create_recipe(client, "Privée de Bob")
    act_as(default_user)

    plan = draw(client, meal_count=2)
    assert {e["recipe"]["name"] for e in plan["entries"]} == {"Ma recette", "Publique de Bob"}

    response = client.post(
        "/plans/draw", json={"week_start": MONDAY, "meal_count": 2, "mine_only": True}
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    "payload",
    [
        {"week_start": "2026-11-10"},  # mardi
        {"meal_count": 0},
        {"meal_count": 8},  # 7 créneaux seulement avec un repas par jour
        {"meal_count": 15, "meals": ["lunch", "dinner"]},
        {"meals": []},
        {"meals": ["dinner", "dinner"]},
        {"meals": ["breakfast"]},
    ],
)
def test_draw_request_validation(
    client: TestClient, seven_recipes: list[dict], payload: dict
) -> None:
    response = client.post("/plans/draw", json={"week_start": MONDAY} | payload)
    assert response.status_code == 422


def test_draw_defaults_to_upcoming_monday(client: TestClient, seven_recipes: list[dict]) -> None:
    response = client.post("/plans/draw", json={})

    assert response.status_code == 201
    assert response.json()["week_start"] == upcoming_monday().isoformat()


@pytest.mark.parametrize(
    ("today", "expected"),
    [
        (date(2026, 11, 9), date(2026, 11, 9)),  # lundi : la semaine en cours
        (date(2026, 11, 11), date(2026, 11, 16)),
        (date(2026, 11, 15), date(2026, 11, 16)),
    ],
)
def test_upcoming_monday(today: date, expected: date) -> None:
    assert upcoming_monday(today) == expected


def test_draw_is_random_but_reproducible(db_session: Session, default_user: User) -> None:
    db_session.add_all(Recipe(owner=default_user, name=f"R{i}") for i in range(10))
    db_session.flush()
    request = DrawRequest(week_start=date(2026, 11, 9), meal_count=3)

    def drawn(seed: int) -> list[uuid.UUID]:
        plan = draw_plan(db_session, default_user, request, rng=random.Random(seed))
        return [entry.recipe_id for entry in plan.entries]

    assert drawn(42) == drawn(42)
    # Sur de nombreux tirages, chaque recette finit par sortir
    counts = Counter(rid for seed in range(60) for rid in drawn(seed))
    assert len(counts) == 10


# --- Consultation / suppression ------------------------------------------------------------------


def test_get_list_and_delete_plans(client: TestClient, seven_recipes: list[dict]) -> None:
    first = draw(client, meal_count=1)
    second = draw(client, meal_count=1, week_start="2026-11-16")

    assert client.get(f"/plans/{first['id']}").json() == first
    # Plus récent d'abord
    assert [p["id"] for p in client.get("/plans").json()] == [second["id"], first["id"]]

    assert client.delete(f"/plans/{first['id']}").status_code == 204
    assert client.get(f"/plans/{first['id']}").status_code == 404
    assert [p["id"] for p in client.get("/plans").json()] == [second["id"]]


def test_plans_are_private(
    client: TestClient,
    seven_recipes: list[dict],
    other_user: User,
    act_as: Callable[[User], None],
) -> None:
    plan = draw(client, meal_count=1)

    act_as(other_user)
    assert client.get("/plans").json() == []
    assert client.get(f"/plans/{plan['id']}").status_code == 404
    assert client.get(f"/plans/{plan['id']}/shopping-list").status_code == 404
    assert client.delete(f"/plans/{plan['id']}").status_code == 404


def test_deleting_plan_unblocks_recipe_deletion(client: TestClient) -> None:
    recipe = create_recipe(client, "Unique")
    plan = draw(client, meal_count=1)

    assert client.delete(f"/recipes/{recipe['id']}").status_code == 409
    assert client.delete(f"/plans/{plan['id']}").status_code == 204
    assert client.delete(f"/recipes/{recipe['id']}").status_code == 204


@pytest.mark.parametrize("path", ["/plans/{id}", "/plans/{id}/shopping-list"])
def test_unknown_plan_returns_404(client: TestClient, path: str) -> None:
    assert client.get(path.format(id=uuid.uuid4())).status_code == 404
