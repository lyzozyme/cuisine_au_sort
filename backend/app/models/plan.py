from __future__ import annotations

import uuid
from datetime import date, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger, UniqueConstraint, case
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Meal, str_enum

if TYPE_CHECKING:
    from app.models.recipe import Recipe
    from app.models.user import User


class WeeklyPlan(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Planning de repas d'une semaine. Toujours privé à son propriétaire."""

    __tablename__ = "weekly_plans"
    __table_args__ = (
        Index("ix_weekly_plans_owner_id_week_start", "owner_id", "week_start"),
        # Les jours des entrées (0 = lundi) sont relatifs à week_start, qui doit donc être un lundi
        CheckConstraint("EXTRACT(ISODOW FROM week_start) = 1", name="week_start_is_monday"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    week_start: Mapped[date]

    owner: Mapped[User] = relationship(back_populates="plans")
    entries: Mapped[list[PlanEntry]] = relationship(
        back_populates="plan",
        cascade="all, delete-orphan",
        passive_deletes=True,
        # Ordre chronologique des repas (déjeuner puis dîner), pas l'ordre alphabétique des valeurs
        order_by=lambda: (
            PlanEntry.day,
            case({meal.value: i for i, meal in enumerate(Meal)}, value=PlanEntry.meal),
        ),
    )


class PlanEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "plan_entries"
    __table_args__ = (
        UniqueConstraint("plan_id", "day", "meal"),
        CheckConstraint("day BETWEEN 0 AND 6", name="day_of_week"),
    )

    plan_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("weekly_plans.id", ondelete="CASCADE"))
    # Jour de la semaine : 0 = lundi … 6 = dimanche, relatif à WeeklyPlan.week_start
    day: Mapped[int] = mapped_column(SmallInteger)
    meal: Mapped[Meal] = mapped_column(str_enum(Meal, "meal"))
    # Peut référencer une recette d'un autre utilisateur (publique/partagée).
    # RESTRICT : une recette ne peut pas être supprimée tant qu'elle figure dans un planning.
    recipe_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("recipes.id", ondelete="RESTRICT"), index=True
    )

    plan: Mapped[WeeklyPlan] = relationship(back_populates="entries")
    recipe: Mapped[Recipe] = relationship()

    @property
    def scheduled_on(self) -> date:
        """Date du repas."""
        return self.plan.week_start + timedelta(days=self.day)
