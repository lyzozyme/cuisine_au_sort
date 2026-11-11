from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.health import HealthRead
from app.services.health import is_database_reachable

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthRead,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": HealthRead}},
)
def health(db: Annotated[Session, Depends(get_db)], response: Response) -> HealthRead:
    if is_database_reachable(db):
        return HealthRead(status="OK", database="OK")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthRead(status="error", database="unreachable")
