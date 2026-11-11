from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import Engine

import app.models  # noqa: F401  (enregistre toutes les tables dans Base.metadata)
from app.db.base import Base


def test_migrations_are_in_sync_with_models(test_engine: Engine) -> None:
    """Échoue si un modèle a été modifié sans générer la migration correspondante."""
    with test_engine.connect() as connection:
        context = MigrationContext.configure(
            connection, opts={"compare_type": True, "compare_server_default": True}
        )
        diff = compare_metadata(context, Base.metadata)

    assert diff == [], f"Migration manquante : uv run alembic revision --autogenerate\n{diff}"
