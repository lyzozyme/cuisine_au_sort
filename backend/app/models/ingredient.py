from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Aisle, Unit, str_enum


class Ingredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Catalogue global d'ingrédients, partagé entre tous les utilisateurs."""

    __tablename__ = "ingredients"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    default_unit: Mapped[Unit] = mapped_column(str_enum(Unit, "unit"))
    aisle: Mapped[Aisle] = mapped_column(str_enum(Aisle, "aisle"), default=Aisle.OTHER)
