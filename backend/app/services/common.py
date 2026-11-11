from sqlalchemy import ColumnElement
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.services.errors import ConflictError


def contains_ignore_case(column: InstrumentedAttribute[str], term: str) -> ColumnElement[bool]:
    """Recherche « contient », insensible à la casse, avec échappement de % et _."""
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return column.ilike(f"%{escaped}%", escape="\\")


def commit_or_conflict(db: Session, message: str) -> None:
    """Commit ; une violation de contrainte (ex. requêtes concurrentes ayant passé les
    vérifications préalables) devient une ConflictError plutôt qu'une erreur 500."""
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ConflictError(message) from exc
