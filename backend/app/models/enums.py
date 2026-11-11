"""Énumérations du domaine.

Stockées en VARCHAR (pas de type ENUM PostgreSQL) : ajouter une valeur ne demande pas de
migration de type, seulement une mise à jour de la contrainte CHECK.
"""

from enum import StrEnum

from sqlalchemy import Enum

ENUM_COLUMN_LENGTH = 32


class Visibility(StrEnum):
    PRIVATE = "private"
    SHARED = "shared"
    PUBLIC = "public"


class Unit(StrEnum):
    """Unités normalisées : les quantités sont converties vers ces unités à la saisie
    (kg -> g, l -> ml…) pour pouvoir être additionnées dans la liste de courses."""

    GRAM = "g"
    MILLILITER = "ml"
    PIECE = "piece"
    TEASPOON = "tsp"
    TABLESPOON = "tbsp"
    PINCH = "pinch"


class Aisle(StrEnum):
    """Rayons du magasin, utilisés pour regrouper la liste de courses."""

    PRODUCE = "produce"  # fruits et légumes
    MEAT = "meat"  # boucherie
    FISH = "fish"  # poissonnerie
    DAIRY = "dairy"  # crèmerie
    BAKERY = "bakery"  # boulangerie
    FROZEN = "frozen"  # surgelés
    GROCERY = "grocery"  # épicerie
    SPICES = "spices"  # épices et condiments
    BEVERAGES = "beverages"  # boissons
    OTHER = "other"


class Meal(StrEnum):
    LUNCH = "lunch"
    DINNER = "dinner"


def str_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """Type SQLAlchemy pour une StrEnum : VARCHAR + CHECK, valeurs (et non noms) stockées."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        create_constraint=True,
        # Longueur fixe avec marge : ajouter une valeur ne demandera pas d'ALTER de la colonne
        length=ENUM_COLUMN_LENGTH,
        values_callable=lambda cls: [member.value for member in cls],
        validate_strings=True,
    )
