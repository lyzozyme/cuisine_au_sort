from decimal import Decimal
from typing import Annotated, ClassVar, Self

from pydantic import BaseModel, ConfigDict, PlainSerializer, model_validator


class ErrorRead(BaseModel):
    detail: str


class ValidationErrorItem(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class ValidationErrorRead(BaseModel):
    """Erreur de validation de la requête (format FastAPI), aussi renvoyée en 422."""

    detail: list[ValidationErrorItem]


class InputModel(BaseModel):
    """Base des schémas d'entrée : les champs inconnus sont refusés (fautes de frappe visibles)."""

    model_config = ConfigDict(extra="forbid")


class PatchModel(InputModel):
    """Base des schémas de mise à jour partielle (PATCH).

    Un champ absent n'est pas modifié. Un champ envoyé à `null` n'est accepté que s'il figure
    dans `nullable_fields` (colonnes nullable) ; sinon la requête est rejetée en 422.
    """

    nullable_fields: ClassVar[frozenset[str]] = frozenset()

    @model_validator(mode="after")
    def _reject_null_for_required_fields(self) -> Self:
        invalid = sorted(
            name
            for name in self.model_fields_set - self.nullable_fields
            if getattr(self, name) is None
        )
        if invalid:
            raise ValueError(f"valeur null interdite pour : {', '.join(invalid)}")
        return self


class ReadModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Les Decimal sont sérialisés en nombre JSON (et non en chaîne, comportement par défaut de Pydantic)
DecimalNumber = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]
