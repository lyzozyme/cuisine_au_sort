from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text
from sqlalchemy.orm import Session

from app.db.config import get_settings
from app.db.session import build_engine, get_db
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _alembic_config(database_url: str) -> Config:
    config = Config(BACKEND_DIR / "alembic.ini")
    config.attributes["database_url"] = database_url
    config.attributes["configure_logger"] = False  # ne pas écraser la config de logs de pytest
    return config


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    """Moteur sur la base de test, recréée de zéro puis migrée jusqu'à la dernière révision.

    Le schéma est supprimé plutôt que rétrogradé : une session précédente a pu laisser la base
    à une révision qui n'existe plus (migration réécrite sur une branche). Le cycle
    upgrade -> downgrade -> upgrade vérifie que chaque migration est réversible.
    """
    settings = get_settings()
    if settings.test_database_url == settings.database_url:
        pytest.exit("TEST_DATABASE_URL doit être différente de DATABASE_URL", returncode=1)

    engine = build_engine(settings.test_database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    config = _alembic_config(settings.test_database_url)
    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    """Session sur la base de test, dans une transaction annulée en fin de test."""
    with test_engine.connect() as connection:
        transaction = connection.begin()
        # Mêmes options que SessionLocal, pour que les tests reflètent la production
        session = Session(
            bind=connection,
            join_transaction_mode="create_savepoint",
            autoflush=False,
            expire_on_commit=False,
        )
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
