"""Conversion des unités saisies vers les unités normalisées stockées en base."""

from decimal import Decimal
from enum import StrEnum

from app.models.enums import Unit


class InputUnit(StrEnum):
    """Unités acceptées à la saisie : les unités normalisées + leurs multiples courants."""

    GRAM = "g"
    KILOGRAM = "kg"
    MILLILITER = "ml"
    CENTILITER = "cl"
    DECILITER = "dl"
    LITER = "l"
    PIECE = "piece"
    TEASPOON = "tsp"
    TABLESPOON = "tbsp"
    PINCH = "pinch"


_CONVERSIONS: dict[InputUnit, tuple[Unit, int]] = {
    InputUnit.KILOGRAM: (Unit.GRAM, 1000),
    InputUnit.CENTILITER: (Unit.MILLILITER, 10),
    InputUnit.DECILITER: (Unit.MILLILITER, 100),
    InputUnit.LITER: (Unit.MILLILITER, 1000),
}


def normalize_quantity(quantity: Decimal, unit: InputUnit) -> tuple[Decimal, Unit]:
    """Ex. (1.5, kg) -> (1500, g). Les unités déjà normalisées sont renvoyées telles quelles."""
    if unit in _CONVERSIONS:
        target, factor = _CONVERSIONS[unit]
        return quantity * factor, target
    return quantity, Unit(unit.value)
