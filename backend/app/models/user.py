from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.plan import WeeklyPlan
    from app.models.recipe import Recipe


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))

    recipes: Mapped[list[Recipe]] = relationship(back_populates="owner", passive_deletes=True)
    plans: Mapped[list[WeeklyPlan]] = relationship(back_populates="owner", passive_deletes=True)
