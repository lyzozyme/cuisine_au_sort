from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.session import get_db
from app.main import app


def test_health_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "OK", "database": "OK"}


def test_health_database_unreachable() -> None:
    failing_session = MagicMock()
    failing_session.execute.side_effect = OperationalError("SELECT 1", {}, Exception("down"))
    app.dependency_overrides[get_db] = lambda: failing_session
    try:
        with TestClient(app) as client:
            response = client.get("/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unreachable"}
