from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import Unit, Visibility, str_enum

if TYPE_CHECKING:
    from app.models.ingredient import Ingredient
    from app.models.user import User


class Recipe(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipes"
    __table_args__ = (
        UniqueConstraint("owner_id", "name"),
        CheckConstraint("servings > 0", name="servings_positive"),
        # Filtrage par tags (tirage au sort avec tags exclus) via l'opérateur && sur le tableau
        Index("ix_recipes_tags", "tags", postgresql_using="gin"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    servings: Mapped[int] = mapped_column(default=2)
    instructions: Mapped[str] = mapped_column(Text, default="", server_default="")
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String(50)), default=list, server_default=text("'{}'")
    )
    visibility: Mapped[Visibility] = mapped_column(
        str_enum(Visibility, "visibility"),
        default=Visibility.PRIVATE,
        server_default=Visibility.PRIVATE.value,
    )
    # Recette d'origine en cas de copie (fork) ; conservée à NULL si l'originale est supprimée
    source_recipe_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("recipes.id", ondelete="SET NULL")
    )

    owner: Mapped[User] = relationship(back_populates="recipes")
    ingredients: Mapped[list[RecipeIngredient]] = relationship(
        back_populates="recipe", cascade="all, delete-orphan", passive_deletes=True
    )
    source_recipe: Mapped[Recipe | None] = relationship(remote_side="Recipe.id")


class RecipeIngredient(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (
        UniqueConstraint("recipe_id", "ingredient_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    recipe_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("recipes.id", ondelete="CASCADE"))
    # RESTRICT : impossible de supprimer un ingrédient du catalogue encore utilisé
    ingredient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("ingredients.id", ondelete="RESTRICT"), index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3))
    unit: Mapped[Unit] = mapped_column(str_enum(Unit, "unit"))

    recipe: Mapped[Recipe] = relationship(back_populates="ingredients")
    ingredient: Mapped[Ingredient] = relationship()
