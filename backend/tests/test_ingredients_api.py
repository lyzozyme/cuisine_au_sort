import uuid

import pytest
from fastapi.testclient import TestClient


def create_ingredient(client: TestClient, name: str = "Farine", **fields) -> dict:
    payload = {"name": name, "default_unit": "g", "aisle": "grocery"} | fields
    response = client.post("/ingredients", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_and_get_ingredient(client: TestClient) -> None:
    created = create_ingredient(client, "  Farine  ")

    assert created["name"] == "Farine"  # espaces retirés
    assert created["default_unit"] == "g"
    assert created["aisle"] == "grocery"
    assert client.get(f"/ingredients/{created['id']}").json() == created


def test_aisle_defaults_to_other(client: TestClient) -> None:
    response = client.post("/ingredients", json={"name": "Truc", "default_unit": "piece"})
    assert response.json()["aisle"] == "other"


@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "default_unit": "g"},
        {"name": "Sel", "default_unit": "kg"},  # unité non normalisée
        {"name": "Sel", "default_unit": "g", "aisle": "inconnu"},
        {"name": "Sel", "default_unit": "g", "unknown_field": 1},
    ],
)
def test_create_ingredient_validation(client: TestClient, payload: dict) -> None:
    assert client.post("/ingredients", json=payload).status_code == 422


def test_ingredient_name_is_unique_ignoring_case(client: TestClient) -> None:
    create_ingredient(client, "Farine")

    response = client.post("/ingredients", json={"name": "FARINE", "default_unit": "g"})
    assert response.status_code == 409
    assert "existe déjà" in response.json()["detail"]


def test_list_ingredients_with_filters(client: TestClient) -> None:
    create_ingredient(client, "Lait", default_unit="ml", aisle="dairy")
    create_ingredient(client, "farine")
    create_ingredient(client, "Beurre", aisle="dairy")

    names = [i["name"] for i in client.get("/ingredients").json()]
    assert names == ["Beurre", "farine", "Lait"]  # tri insensible à la casse
    assert [i["name"] for i in client.get("/ingredients", params={"q": "AI"}).json()] == ["Lait"]
    dairy = client.get("/ingredients", params={"aisle": "dairy"}).json()
    assert [i["name"] for i in dairy] == ["Beurre", "Lait"]
    page = client.get("/ingredients", params={"limit": 1, "offset": 1}).json()
    assert [i["name"] for i in page] == ["farine"]


def test_search_escapes_like_wildcards(client: TestClient) -> None:
    create_ingredient(client, "Farine")
    assert client.get("/ingredients", params={"q": "%"}).json() == []


def test_update_ingredient(client: TestClient) -> None:
    created = create_ingredient(client)

    response = client.patch(f"/ingredients/{created['id']}", json={"aisle": "bakery"})

    assert response.status_code == 200
    body = response.json()
    assert (body["name"], body["aisle"]) == ("Farine", "bakery")


def test_update_ingredient_rejects_null_and_duplicate_name(client: TestClient) -> None:
    flour = create_ingredient(client, "Farine")
    create_ingredient(client, "Sucre")

    assert client.patch(f"/ingredients/{flour['id']}", json={"name": None}).status_code == 422
    assert client.patch(f"/ingredients/{flour['id']}", json={"name": "sucre"}).status_code == 409
    # Changer la casse de son propre nom reste possible
    assert client.patch(f"/ingredients/{flour['id']}", json={"name": "FARINE"}).status_code == 200


def test_delete_ingredient(client: TestClient) -> None:
    created = create_ingredient(client)

    assert client.delete(f"/ingredients/{created['id']}").status_code == 204
    assert client.get(f"/ingredients/{created['id']}").status_code == 404


def test_ingredient_used_in_recipe_cannot_be_deleted(client: TestClient) -> None:
    flour = create_ingredient(client)
    recipe = {"name": "Crêpes", "ingredients": [{"ingredient_id": flour["id"], "quantity": 250}]}
    assert client.post("/recipes", json=recipe).status_code == 201

    response = client.delete(f"/ingredients/{flour['id']}")

    assert response.status_code == 409
    assert "1 recette" in response.json()["detail"]


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_unknown_ingredient_returns_404(client: TestClient, method: str) -> None:
    kwargs = {"json": {"aisle": "dairy"}} if method == "patch" else {}
    response = client.request(method, f"/ingredients/{uuid.uuid4()}", **kwargs)
    assert response.status_code == 404
