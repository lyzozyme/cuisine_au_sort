import uuid
from collections.abc import Sequence

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import Ingredient, PlanEntry, Recipe, RecipeIngredient, User, Visibility
from app.schemas.recipe import RecipeCreate, RecipeIngredientIn, RecipeUpdate
from app.services.common import commit_or_conflict, contains_ignore_case
from app.services.errors import ConflictError, ForbiddenError, InvalidInputError, NotFoundError
from app.services.units import normalize_quantity


def visible_recipes_condition(user: User) -> ColumnElement[bool]:
    """Règle de visibilité des recettes : SEUL endroit où elle est définie.

    Visible si : propriétaire OU publique OU partagée avec l'utilisateur.
    Le partage (RecipeShare) n'existe pas encore : une recette `shared` n'est pour l'instant
    visible que de son propriétaire. L'ajouter ici le moment venu.
    """
    return or_(Recipe.owner_id == user.id, Recipe.visibility == Visibility.PUBLIC)


def _with_ingredients(query):
    return query.options(selectinload(Recipe.ingredients).joinedload(RecipeIngredient.ingredient))


def list_recipes(
    db: Session,
    user: User,
    *,
    search: str | None = None,
    tag: str | None = None,
    mine: bool = False,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[Recipe]:
    query = (
        _with_ingredients(select(Recipe))
        .where(Recipe.owner_id == user.id if mine else visible_recipes_condition(user))
        .order_by(func.lower(Recipe.name), Recipe.id)
        .limit(limit)
        .offset(offset)
    )
    if search:
        query = query.where(contains_ignore_case(Recipe.name, search))
    if tag:
        query = query.where(Recipe.tags.contains([tag.strip().lower()]))
    return db.scalars(query).all()


def get_recipe(db: Session, user: User, recipe_id: uuid.UUID) -> Recipe:
    """Recette visible par l'utilisateur. Une recette invisible est signalée comme introuvable,
    pour ne pas révéler son existence."""
    recipe = db.scalars(
        _with_ingredients(select(Recipe)).where(
            Recipe.id == recipe_id, visible_recipes_condition(user)
        )
    ).one_or_none()
    if recipe is None:
        raise NotFoundError("Recette introuvable")
    return recipe


def _get_owned_recipe(db: Session, user: User, recipe_id: uuid.UUID) -> Recipe:
    recipe = get_recipe(db, user, recipe_id)
    if recipe.owner_id != user.id:
        raise ForbiddenError("Seul le propriétaire peut modifier ou supprimer cette recette")
    return recipe


def _ensure_name_available(
    db: Session, user: User, name: str, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(Recipe.id).where(Recipe.owner_id == user.id, Recipe.name == name)
    if exclude_id is not None:
        query = query.where(Recipe.id != exclude_id)
    if db.scalars(query).first() is not None:
        raise ConflictError(f"Vous avez déjà une recette nommée « {name} »")


def _load_ingredients(db: Session, items: list[RecipeIngredientIn]) -> dict[uuid.UUID, Ingredient]:
    ids = {item.ingredient_id for item in items}
    found = {i.id: i for i in db.scalars(select(Ingredient).where(Ingredient.id.in_(ids)))}
    if missing := ids - found.keys():
        raise InvalidInputError(f"Ingrédient(s) inconnu(s) : {', '.join(map(str, missing))}")
    return found


def _set_ingredients(db: Session, recipe: Recipe, items: list[RecipeIngredientIn]) -> None:
    """Remplace la liste d'ingrédients de la recette.

    Les lignes existantes sont mises à jour sur place plutôt que supprimées puis recréées :
    SQLAlchemy exécute les INSERT avant les DELETE, ce qui violerait la contrainte
    UNIQUE(recipe_id, ingredient_id) pour un ingrédient conservé.
    """
    catalog = _load_ingredients(db, items)
    existing = {line.ingredient_id: line for line in recipe.ingredients}
    lines = []
    for item in items:
        ingredient = catalog[item.ingredient_id]
        if item.unit is None:
            quantity, unit = item.quantity, ingredient.default_unit
        else:
            quantity, unit = normalize_quantity(item.quantity, item.unit)
        line = existing.get(item.ingredient_id) or RecipeIngredient(ingredient=ingredient)
        line.quantity, line.unit = quantity, unit
        lines.append(line)
    recipe.ingredients = lines  # les lignes absentes sont supprimées (delete-orphan)


def create_recipe(db: Session, user: User, data: RecipeCreate) -> Recipe:
    _ensure_name_available(db, user, data.name)
    recipe = Recipe(owner=user, **data.model_dump(exclude={"ingredients"}))
    _set_ingredients(db, recipe, data.ingredients)
    db.add(recipe)
    commit_or_conflict(db, f"Vous avez déjà une recette nommée « {data.name} »")
    return get_recipe(db, user, recipe.id)


def update_recipe(db: Session, user: User, recipe_id: uuid.UUID, data: RecipeUpdate) -> Recipe:
    recipe = _get_owned_recipe(db, user, recipe_id)
    if data.name is not None:
        _ensure_name_available(db, user, data.name, exclude_id=recipe.id)
    for field, value in data.model_dump(exclude_unset=True, exclude={"ingredients"}).items():
        setattr(recipe, field, value)
    if data.ingredients is not None:
        _set_ingredients(db, recipe, data.ingredients)
        recipe.updated_at = func.now()  # la ligne recipes peut ne pas changer elle-même
    commit_or_conflict(db, f"Vous avez déjà une recette nommée « {recipe.name} »")
    db.expire(recipe)  # recharge updated_at et les ingrédients
    return get_recipe(db, user, recipe.id)


def delete_recipe(db: Session, user: User, recipe_id: uuid.UUID) -> None:
    recipe = _get_owned_recipe(db, user, recipe_id)
    plan_count = db.scalar(
        select(func.count(func.distinct(PlanEntry.plan_id))).where(PlanEntry.recipe_id == recipe.id)
    )
    if plan_count:
        raise ConflictError(
            f"Recette utilisée dans {plan_count} planning(s) : retirez-la avant de la supprimer"
        )
    db.delete(recipe)
    commit_or_conflict(db, "Recette utilisée dans un planning : suppression impossible")
