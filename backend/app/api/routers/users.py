from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.user import UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(user: CurrentUser):
    """Utilisateur courant (le frontend s'en sert pour savoir quelles recettes il peut modifier)."""
    return user
