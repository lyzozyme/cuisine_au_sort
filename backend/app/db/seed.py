"""Données initiales. Idempotent : peut être relancé sans effet de bord.

Usage (depuis backend/, après `alembic upgrade head`) :
    uv run python -m app.db.seed
"""

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.config import get_settings
from app.db.session import SessionLocal
from app.models import User


def seed_default_user(session: Session) -> User:
    """Crée l'utilisateur par défaut s'il n'existe pas, et le renvoie."""
    settings = get_settings()
    session.execute(
        insert(User)
        .values(email=settings.default_user_email, display_name=settings.default_user_display_name)
        .on_conflict_do_nothing(index_elements=[User.email])
    )
    return session.scalars(select(User).where(User.email == settings.default_user_email)).one()


def main() -> None:
    with SessionLocal.begin() as session:
        user = seed_default_user(session)
        print(f"Utilisateur par défaut : {user.email} ({user.id})")


if __name__ == "__main__":
    main()
