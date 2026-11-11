from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models import User


def test_read_current_user(
    client: TestClient, default_user: User, other_user: User, act_as: Callable[[User], None]
) -> None:
    assert client.get("/users/me").json() == {
        "id": str(default_user.id),
        "email": default_user.email,
        "display_name": default_user.display_name,
    }

    act_as(other_user)
    assert client.get("/users/me").json()["id"] == str(other_user.id)
