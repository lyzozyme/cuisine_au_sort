# CuisineAuSort

Application web pour enregistrer des recettes, tirer au sort les repas d'une semaine et en déduire une liste de courses.

## Architecture

Monorepo avec deux applications distinctes :

```
cuisineausort/
├── backend/          # API Python : FastAPI + SQLAlchemy 2.x + PostgreSQL
├── frontend/         # Interface utilisateur (framework à définir, suggestion : React + Vite + TypeScript)
├── docker-compose.yml
└── .github/workflows/
```

## Backend — stack et conventions

- Python 3.12+, gestion des dépendances avec **uv**
- **FastAPI**, **SQLAlchemy 2.x** (style `Mapped[...]`), **Alembic** pour les migrations, **PostgreSQL** (via Docker Compose en local)
- Configuration via **pydantic-settings** et fichier `.env` (jamais commité ; fournir `.env.example`)
- Structure :
  - `app/models` : modèles SQLAlchemy
  - `app/schemas` : schémas Pydantic (entrée/sortie API)
  - `app/api/routers` : routes FastAPI (fines, sans logique métier)
  - `app/services` : logique métier (tirage, agrégation liste de courses, règles de visibilité)
  - `app/db` : session, base, configuration
- Tests avec **pytest** sur une base PostgreSQL de test ; lint/format avec **ruff**
- CORS activé pour le frontend

## Modèle de données

Conçu dès le départ pour un futur usage multi-utilisateur avec partage de recettes (non implémenté au début).

- **User** : `id`, `email`, `display_name`, `created_at`. Au départ, un seul utilisateur par défaut créé par seed.
- **Recipe** : `id`, `owner_id` → User, `name`, `description`, `servings`, `instructions`, `tags`, `visibility` (`private` | `shared` | `public`, défaut `private`), `source_recipe_id` (nullable, pour les copies/forks), `created_at`, `updated_at`. Contrainte `UNIQUE(owner_id, name)`.
- **Ingredient** : catalogue **global** partagé. `id`, `name` (unique), `default_unit`, `aisle` (rayon). Plus tard : `created_by` nullable pour les ingrédients personnalisés.
- **RecipeIngredient** : `recipe_id`, `ingredient_id`, `quantity`, `unit`.
- **WeeklyPlan** : `id`, `owner_id` → User, `week_start`, timestamps. Toujours privé.
- **PlanEntry** : `plan_id`, `day`, `meal`, `recipe_id` (peut pointer vers une recette dont l'utilisateur n'est pas propriétaire).
- Plus tard : **RecipeShare** (`recipe_id`, `user_id`, `permission`).

Règles :
- Identifiants **UUID** partout.
- `created_at` / `updated_at` sur toutes les tables.
- **Unités normalisées** (g, ml, pièce…) pour permettre l'agrégation dans la liste de courses.

## Authentification et accès

- Toutes les routes (sauf `/health`, public pour la supervision) passent par une dépendance FastAPI `get_current_user`. Au départ elle renvoie l'utilisateur par défaut ; plus tard elle décodera un token (JWT ou OIDC), sans modifier les routes.
- Le filtrage par utilisateur se fait **dans la couche service**, centralisé dans une seule fonction : une recette est visible si `owner_id == me` OR `visibility == public` OR partagée avec moi.

## Fonctionnalités cibles de l'API

1. CRUD ingrédients
2. CRUD recettes (avec leurs ingrédients)
3. `POST /plans/draw` : tirage au sort (nombre de repas, tags exclus, pas de doublons)
4. `GET /plans/{id}/shopping-list` : agrégation des quantités par ingrédient/unité, regroupées par rayon
5. `GET /health` : vérifie la connexion à la base

## Feuille de route

1. Initialiser le monorepo, `docker-compose.yml` avec PostgreSQL
2. Squelette FastAPI + `/health` + configuration
3. Modèles SQLAlchemy + première migration Alembic + seed utilisateur par défaut
4. CRUD ingrédients et recettes + tests
5. Tirage au sort + liste de courses + tests
6. Frontend (client API généré depuis l'OpenAPI de FastAPI, ex. `openapi-typescript`)
7. Dockerfiles, CI GitHub Actions (lint, tests, build, filtrée par dossier), déploiement
8. Plus tard : authentification réelle, partage de recettes (`RecipeShare`)
