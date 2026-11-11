from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import User
from app.services.users import get_default_user

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(db: DbSession) -> User:
    """Utilisateur à l'origine de la requête.

    Pour l'instant : l'utilisateur par défaut. Plus tard : décodage d'un token (JWT/OIDC) —
    seule cette fonction changera, pas les routes.
    """
    user = get_default_user(db)
    if user is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "Utilisateur par défaut absent : lancer `uv run python -m app.db.seed`",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
