from alembic import command
from alembic.config import Config
from sqlalchemy import Engine


def test_migrations_are_in_sync_with_models(test_engine: Engine, alembic_config: Config) -> None:
    """Échoue si un modèle a été modifié sans générer la migration correspondante.

    Même vérification que `uv run alembic check`, avec les options de comparaison d'alembic/env.py.
    """
    command.check(alembic_config)
