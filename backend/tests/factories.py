"""Création de données de test via l'API."""

from fastapi.testclient import TestClient

MONDAY = "2026-11-09"


def create_ingredient(
    client: TestClient, name: str, default_unit: str = "g", aisle: str = "grocery"
) -> dict:
    response = client.post(
        "/ingredients", json={"name": name, "default_unit": default_unit, "aisle": aisle}
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_recipe(client: TestClient, name: str, **fields) -> dict:
    response = client.post("/recipes", json={"name": name} | fields)
    assert response.status_code == 201, response.text
    return response.json()


def draw(client: TestClient, **fields) -> dict:
    response = client.post("/plans/draw", json={"week_start": MONDAY} | fields)
    assert response.status_code == 201, response.text
    return response.json()
