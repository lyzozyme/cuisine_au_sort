from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.db.config import get_settings
from app.db.session import build_engine, get_db
from app.main import app


@pytest.fixture(scope="session")
def test_engine():
    engine = build_engine(get_settings().test_database_url)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Iterator[Session]:
    """Session sur la base de test, dans une transaction annulée en fin de test."""
    with test_engine.connect() as connection:
        transaction = connection.begin()
        session = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")()
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
