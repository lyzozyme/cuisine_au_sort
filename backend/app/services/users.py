from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.config import get_settings
from app.models import User


def get_default_user(db: Session) -> User | None:
    """Utilisateur unique tant qu'il n'y a pas d'authentification (créé par app.db.seed)."""
    email = get_settings().default_user_email
    return db.scalars(select(User).where(User.email == email)).one_or_none()
