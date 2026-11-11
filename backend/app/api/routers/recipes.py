import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.api.errors import error_responses
from app.schemas.recipe import RecipeCreate, RecipeRead, RecipeUpdate
from app.services import recipes as service

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=list[RecipeRead])
def list_recipes(
    db: DbSession,
    user: CurrentUser,
    q: Annotated[str | None, Query(max_length=200, description="Recherche dans le nom")] = None,
    tag: Annotated[str | None, Query(max_length=50)] = None,
    mine: Annotated[bool, Query(description="Uniquement mes recettes")] = False,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    return service.list_recipes(db, user, search=q, tag=tag, mine=mine, limit=limit, offset=offset)


@router.post(
    "",
    response_model=RecipeRead,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409, 422),
)
def create_recipe(db: DbSession, user: CurrentUser, data: RecipeCreate):
    return service.create_recipe(db, user, data)


@router.get("/{recipe_id}", response_model=RecipeRead, responses=error_responses(404))
def get_recipe(db: DbSession, user: CurrentUser, recipe_id: uuid.UUID):
    return service.get_recipe(db, user, recipe_id)


@router.patch(
    "/{recipe_id}", response_model=RecipeRead, responses=error_responses(403, 404, 409, 422)
)
def update_recipe(db: DbSession, user: CurrentUser, recipe_id: uuid.UUID, data: RecipeUpdate):
    return service.update_recipe(db, user, recipe_id, data)


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(403, 404, 409),
)
def delete_recipe(db: DbSession, user: CurrentUser, recipe_id: uuid.UUID) -> None:
    service.delete_recipe(db, user, recipe_id)
