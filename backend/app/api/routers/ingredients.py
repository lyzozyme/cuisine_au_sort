import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DbSession, get_current_user
from app.api.errors import error_responses
from app.models import Aisle
from app.schemas.ingredient import IngredientCreate, IngredientRead, IngredientUpdate
from app.services import ingredients as service

# Catalogue global : l'utilisateur n'est pas utilisé, mais l'authentification reste requise
router = APIRouter(
    prefix="/ingredients", tags=["ingredients"], dependencies=[Depends(get_current_user)]
)


@router.get("", response_model=list[IngredientRead])
def list_ingredients(
    db: DbSession,
    q: Annotated[str | None, Query(max_length=100, description="Recherche dans le nom")] = None,
    aisle: Aisle | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return service.list_ingredients(db, search=q, aisle=aisle, limit=limit, offset=offset)


@router.post(
    "",
    response_model=IngredientRead,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409),
)
def create_ingredient(db: DbSession, data: IngredientCreate):
    return service.create_ingredient(db, data)


@router.get("/{ingredient_id}", response_model=IngredientRead, responses=error_responses(404))
def get_ingredient(db: DbSession, ingredient_id: uuid.UUID):
    return service.get_ingredient(db, ingredient_id)


@router.patch(
    "/{ingredient_id}", response_model=IngredientRead, responses=error_responses(404, 409)
)
def update_ingredient(db: DbSession, ingredient_id: uuid.UUID, data: IngredientUpdate):
    return service.update_ingredient(db, ingredient_id, data)


@router.delete(
    "/{ingredient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(404, 409),
)
def delete_ingredient(db: DbSession, ingredient_id: uuid.UUID) -> None:
    service.delete_ingredient(db, ingredient_id)
