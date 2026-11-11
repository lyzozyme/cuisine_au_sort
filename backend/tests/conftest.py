from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, make_url, text
from sqlalchemy.orm import Session

from app.db.config import get_settings
from app.db.session import SessionLocal, build_engine, get_db
from app.main import app

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    """Configuration Alembic pointant sur la base de test (même env.py que la CLI)."""
    config = Config(BACKEND_DIR / "alembic.ini")
    config.attributes["database_url"] = get_settings().test_database_url
    config.attributes["configure_logger"] = False  # ne pas écraser la config de logs de pytest
    return config


@pytest.fixture(scope="session")
def test_engine(alembic_config: Config) -> Iterator[Engine]:
    """Moteur sur la base de test, recréée de zéro puis migrée jusqu'à la dernière révision.

    Le schéma est supprimé plutôt que rétrogradé : une session précédente a pu laisser la base
    à une révision qui n'existe plus (migration réécrite sur une branche). Le cycle
    upgrade -> downgrade -> upgrade vérifie que chaque migration est réversible.
    """
    settings = get_settings()
    # Comparaison sur l'URL analysée (et non la chaîne brute) : localhost/127.0.0.1, mot de passe
    # ou paramètres différents ne doivent pas permettre de vider la base de développement.
    test_db = make_url(settings.test_database_url).database
    if test_db == make_url(settings.database_url).database or "test" not in (test_db or ""):
        pytest.exit(
            "TEST_DATABASE_URL doit désigner une base de test distincte de DATABASE_URL",
            returncode=1,
        )

    engine = build_engine(settings.test_database_url)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    """Session sur la base de test, dans une transaction annulée en fin de test."""
    with test_engine.connect() as connection:
        transaction = connection.begin()
        # Hérite des options de SessionLocal, pour que les tests reflètent la production
        session = SessionLocal(bind=connection, join_transaction_mode="create_savepoint")
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
