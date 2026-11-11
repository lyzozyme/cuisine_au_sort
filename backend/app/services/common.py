from sqlalchemy import ColumnElement
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.services.errors import ConflictError


def contains_ignore_case(column: InstrumentedAttribute[str], term: str) -> ColumnElement[bool]:
    """Recherche « contient », insensible à la casse, avec échappement de % et _."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


CONCURRENT_CHANGE_MESSAGE = "Conflit avec une modification concurrente : réessayez"


def commit_or_conflict(db: Session, message: str, *, constraint: str) -> None:
    """Commit ; une violation de contrainte (ex. requêtes concurrentes ayant passé les
    vérifications préalables) devient une ConflictError plutôt qu'une erreur 500.

    `message` n'est utilisé que si la contrainte violée est `constraint` ; toute autre violation
    (ex. ingrédient supprimé entre-temps) reçoit un message générique.
    """
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        violated = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        raise ConflictError(
            message if violated == constraint else CONCURRENT_CHANGE_MESSAGE
        ) from exc
