import uuid
from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Meal, PlanEntry, User, WeeklyPlan


@pytest.fixture
def flour(client: TestClient) -> dict:
    return client.post(
        "/ingredients", json={"name": "Farine", "default_unit": "g", "aisle": "grocery"}
    ).json()


@pytest.fixture
def milk(client: TestClient) -> dict:
    return client.post(
        "/ingredients", json={"name": "Lait", "default_unit": "ml", "aisle": "dairy"}
    ).json()


def create_recipe(client: TestClient, name: str = "Crêpes", **fields) -> dict:
    response = client.post("/recipes", json={"name": name} | fields)
    assert response.status_code == 201, response.text
    return response.json()


def lines(recipe: dict) -> list[tuple[str, float, str]]:
    return [(i["ingredient"]["name"], i["quantity"], i["unit"]) for i in recipe["ingredients"]]


# --- Création / lecture -------------------------------------------------------------------------


def test_create_recipe_with_ingredients(
    client: TestClient, default_user: User, flour: dict, milk: dict
) -> None:
    recipe = create_recipe(
        client,
        description="Pour la Chandeleur",
        servings=4,
        instructions="Mélanger, laisser reposer, cuire.",
        tags=[" Dessert ", "rapide", "dessert"],
        ingredients=[
            {"ingredient_id": milk["id"], "quantity": 0.5, "unit": "l"},
            {"ingredient_id": flour["id"], "quantity": 250},  # unité par défaut : g
        ],
    )

    assert recipe["owner_id"] == str(default_user.id)
    assert recipe["visibility"] == "private"
    assert recipe["tags"] == ["dessert", "rapide"]  # normalisés et dédoublonnés
    assert recipe["source_recipe_id"] is None
    # Unités normalisées (0,5 l -> 500 ml), ingrédients triés par nom
    assert lines(recipe) == [("Farine", 250, "g"), ("Lait", 500, "ml")]
    assert client.get(f"/recipes/{recipe['id']}").json() == recipe


def test_create_minimal_recipe_uses_defaults(client: TestClient) -> None:
    recipe = create_recipe(client)
    assert (recipe["servings"], recipe["instructions"], recipe["tags"]) == (2, "", [])
    assert recipe["description"] is None and recipe["ingredients"] == []


@pytest.mark.parametrize(
    ("unit", "quantity", "expected"),
    [
        ("kg", 1.5, (1500, "g")),
        ("cl", 25, (250, "ml")),
        ("dl", 2, (200, "ml")),
        ("tbsp", 2, (2, "tbsp")),
    ],
)
def test_quantities_are_normalized(
    client: TestClient, flour: dict, unit: str, quantity: float, expected: tuple
) -> None:
    recipe = create_recipe(
        client, ingredients=[{"ingredient_id": flour["id"], "quantity": quantity, "unit": unit}]
    )
    assert lines(recipe) == [("Farine", *expected)]


@pytest.mark.parametrize(
    "ingredient_line",
    [
        {"quantity": 0},
        {"quantity": -1},
        {"quantity": 10_000},
        {"quantity": 0.0001},
        {"quantity": 1, "unit": "boisseau"},
    ],
)
def test_invalid_ingredient_line_is_rejected(
    client: TestClient, flour: dict, ingredient_line: dict
) -> None:
    payload = {"name": "X", "ingredients": [{"ingredient_id": flour["id"]} | ingredient_line]}
    assert client.post("/recipes", json=payload).status_code == 422


def test_duplicate_ingredient_in_recipe_is_rejected(client: TestClient, flour: dict) -> None:
    line = {"ingredient_id": flour["id"], "quantity": 1}
    response = client.post("/recipes", json={"name": "X", "ingredients": [line, line]})
    assert response.status_code == 422


def test_unknown_ingredient_is_rejected(client: TestClient) -> None:
    line = {"ingredient_id": str(uuid.uuid4()), "quantity": 1}
    response = client.post("/recipes", json={"name": "X", "ingredients": [line]})
    assert response.status_code == 422
    assert "inconnu" in response.json()["detail"]


def test_recipe_name_is_unique_per_owner(
    client: TestClient, other_user: User, act_as: Callable[[User], None]
) -> None:
    create_recipe(client, "Ratatouille")
    assert client.post("/recipes", json={"name": "Ratatouille"}).status_code == 409

    act_as(other_user)
    assert client.post("/recipes", json={"name": "Ratatouille"}).status_code == 201


# --- Liste ---------------------------------------------------------------------------------------


def test_list_recipes_with_filters(client: TestClient) -> None:
    create_recipe(client, "Salade niçoise", tags=["été", "rapide"])
    create_recipe(client, "bœuf bourguignon", tags=["viande"])
    create_recipe(client, "Soupe", tags=["hiver"])

    def names(**params) -> list[str]:
        return [r["name"] for r in client.get("/recipes", params=params).json()]

    assert names() == ["bœuf bourguignon", "Salade niçoise", "Soupe"]
    assert names(q="SOU") == ["Soupe"]
    assert names(tag="Rapide") == ["Salade niçoise"]
    assert names(limit=1, offset=2) == ["Soupe"]


# --- Visibilité ----------------------------------------------------------------------------------


def test_visibility_rules(
    client: TestClient, default_user: User, other_user: User, act_as: Callable[[User], None]
) -> None:
    private = create_recipe(client, "Privée")
    shared = create_recipe(client, "Partagée", visibility="shared")
    public = create_recipe(client, "Publique", visibility="public")

    act_as(other_user)
    mine = create_recipe(client, "À Bob")
    listed = {r["name"] for r in client.get("/recipes").json()}
    # Partage (RecipeShare) pas encore implémenté : « shared » reste invisible des autres
    assert listed == {"Publique", "À Bob"}
    assert [r["name"] for r in client.get("/recipes", params={"mine": True}).json()] == ["À Bob"]
    assert client.get(f"/recipes/{private['id']}").status_code == 404
    assert client.get(f"/recipes/{shared['id']}").status_code == 404
    assert client.get(f"/recipes/{public['id']}").status_code == 200

    act_as(default_user)
    assert client.get(f"/recipes/{mine['id']}").status_code == 404


def test_only_owner_can_modify_or_delete(
    client: TestClient, other_user: User, act_as: Callable[[User], None]
) -> None:
    public = create_recipe(client, "Publique", visibility="public")
    private = create_recipe(client, "Privée")

    act_as(other_user)
    assert client.patch(f"/recipes/{public['id']}", json={"servings": 8}).status_code == 403
    assert client.delete(f"/recipes/{public['id']}").status_code == 403
    # Recette invisible : 404, son existence n'est pas révélée
    assert client.patch(f"/recipes/{private['id']}", json={"servings": 8}).status_code == 404
    assert client.delete(f"/recipes/{private['id']}").status_code == 404


# --- Mise à jour ---------------------------------------------------------------------------------


def test_partial_update_keeps_other_fields(client: TestClient, flour: dict) -> None:
    recipe = create_recipe(
        client,
        description="Desc",
        tags=["dessert"],
        ingredients=[{"ingredient_id": flour["id"], "quantity": 250}],
    )

    response = client.patch(
        f"/recipes/{recipe['id']}", json={"servings": 6, "visibility": "public"}
    )

    assert response.status_code == 200
    updated = response.json()
    assert (updated["servings"], updated["visibility"]) == (6, "public")
    assert (updated["description"], updated["tags"]) == ("Desc", ["dessert"])
    assert lines(updated) == [("Farine", 250, "g")]


def test_update_can_clear_description_but_not_name(client: TestClient) -> None:
    recipe = create_recipe(client, description="Desc")

    response = client.patch(f"/recipes/{recipe['id']}", json={"description": None})
    assert response.status_code == 200 and response.json()["description"] is None
    assert client.patch(f"/recipes/{recipe['id']}", json={"name": None}).status_code == 422


def test_update_replaces_ingredient_list(client: TestClient, flour: dict, milk: dict) -> None:
    recipe = create_recipe(
        client,
        ingredients=[
            {"ingredient_id": flour["id"], "quantity": 250},
            {"ingredient_id": milk["id"], "quantity": 500},
        ],
    )

    # Farine conservée avec une nouvelle quantité, lait retiré
    response = client.patch(
        f"/recipes/{recipe['id']}",
        json={"ingredients": [{"ingredient_id": flour["id"], "quantity": 0.3, "unit": "kg"}]},
    )

    assert response.status_code == 200, response.text
    updated = response.json()
    assert lines(updated) == [("Farine", 300, "g")]
    # (updated_at n'est pas vérifié : now() est figé pendant la transaction englobante du test)


def test_rename_to_existing_name_conflicts(client: TestClient) -> None:
    create_recipe(client, "Soupe")
    recipe = create_recipe(client, "Salade")
    assert client.patch(f"/recipes/{recipe['id']}", json={"name": "Soupe"}).status_code == 409


# --- Suppression ---------------------------------------------------------------------------------


def test_delete_recipe(client: TestClient, flour: dict) -> None:
    recipe = create_recipe(client, ingredients=[{"ingredient_id": flour["id"], "quantity": 1}])

    assert client.delete(f"/recipes/{recipe['id']}").status_code == 204
    assert client.get(f"/recipes/{recipe['id']}").status_code == 404
    # L'ingrédient n'est plus utilisé : il peut maintenant être supprimé
    assert client.delete(f"/ingredients/{flour['id']}").status_code == 204


def test_planned_recipe_cannot_be_deleted(
    client: TestClient, db_session: Session, default_user: User
) -> None:
    recipe = create_recipe(client)
    plan = WeeklyPlan(owner=default_user, week_start=date(2026, 11, 9))
    plan.entries.append(PlanEntry(day=0, meal=Meal.DINNER, recipe_id=uuid.UUID(recipe["id"])))
    db_session.add(plan)
    db_session.flush()

    response = client.delete(f"/recipes/{recipe['id']}")

    assert response.status_code == 409
    assert "1 planning" in response.json()["detail"]
    assert client.get(f"/recipes/{recipe['id']}").status_code == 200


def test_routes_require_the_default_user(client: TestClient, db_session: Session) -> None:
    db_session.query(User).delete()
    db_session.flush()

    response = client.get("/recipes")
    assert response.status_code == 500
    assert "seed" in response.json()["detail"]
