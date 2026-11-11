import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.api.deps import CurrentUser, DbSession
from app.api.errors import error_responses
from app.schemas.plan import DrawRequest, PlanRead
from app.schemas.shopping_list import ShoppingListRead
from app.services import plans as service
from app.services.shopping_list import build_shopping_list

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post(
    "/draw",
    response_model=PlanRead,
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409, 422),
)
def draw_plan(db: DbSession, user: CurrentUser, request: DrawRequest):
    """Tire au sort les repas d'une semaine (sans doublon) et enregistre le planning."""
    return service.draw_plan(db, user, request)


@router.get("", response_model=list[PlanRead])
def list_plans(
    db: DbSession,
    user: CurrentUser,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Mes plannings, du plus récent au plus ancien."""
    return service.list_plans(db, user, limit=limit, offset=offset)


@router.get("/{plan_id}", response_model=PlanRead, responses=error_responses(404))
def get_plan(db: DbSession, user: CurrentUser, plan_id: uuid.UUID):
    return service.get_plan(db, user, plan_id)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT, responses=error_responses(404))
def delete_plan(db: DbSession, user: CurrentUser, plan_id: uuid.UUID) -> None:
    service.delete_plan(db, user, plan_id)


@router.get(
    "/{plan_id}/shopping-list", response_model=ShoppingListRead, responses=error_responses(404)
)
def get_shopping_list(
    db: DbSession,
    user: CurrentUser,
    plan_id: uuid.UUID,
    servings: Annotated[
        int | None,
        Query(ge=1, le=100, description="Ramener chaque recette à ce nombre de personnes"),
    ] = None,
):
    """Quantités agrégées par ingrédient et par unité, regroupées par rayon."""
    return build_shopping_list(db, user, plan_id, servings=servings)
