"""Erreurs métier levées par la couche service, traduites en réponses HTTP par app/api/errors.py.

Les services ne connaissent pas HTTP : ils lèvent ces exceptions, l'API choisit le code de statut.
"""


class DomainError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    """Ressource inexistante, ou invisible pour l'utilisateur courant."""


class ForbiddenError(DomainError):
    """Ressource visible mais action non autorisée (ex. modifier la recette d'un autre)."""


class ConflictError(DomainError):
    """Action incompatible avec l'état actuel (doublon, ressource encore utilisée…)."""


class InvalidInputError(DomainError):
    """Requête bien formée mais incohérente avec les données (ex. ingrédient inconnu)."""
