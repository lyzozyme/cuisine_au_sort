from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.schemas.common import ErrorRead
from app.services.errors import (
    ConflictError,
    DomainError,
    ForbiddenError,
    InvalidInputError,
    NotFoundError,
)

_STATUS_BY_ERROR: dict[type[DomainError], int] = {
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ForbiddenError: status.HTTP_403_FORBIDDEN,
    ConflictError: status.HTTP_409_CONFLICT,
    InvalidInputError: status.HTTP_422_UNPROCESSABLE_CONTENT,
}


def _domain_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    status_code = next(
        (code for cls, code in _STATUS_BY_ERROR.items() if isinstance(exc, cls)),
        status.HTTP_400_BAD_REQUEST,
    )
    return JSONResponse(ErrorRead(detail=exc.message).model_dump(), status_code=status_code)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error_handler)


def error_responses(*status_codes: int) -> dict[int | str, dict]:
    """Documente les erreurs métier d'une route dans l'OpenAPI (utile au client généré)."""
    return {code: {"model": ErrorRead} for code in status_codes}
