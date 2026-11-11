# Backend CuisineAuSort

API FastAPI + SQLAlchemy 2.x + PostgreSQL, dépendances gérées avec [uv](https://docs.astral.sh/uv/).

## Démarrage

```bash
# depuis la racine du dépôt : lancer PostgreSQL
docker compose up -d db

# depuis backend/
cp .env.example .env
uv sync
uv run alembic upgrade head     # crée / met à jour le schéma
uv run python -m app.db.seed    # crée l'utilisateur par défaut (idempotent)
uv run uvicorn app.main:app --reload

# ou depuis la racine du dépôt
uv run --directory backend uvicorn app.main:app --reload
```

> L'argument d'uvicorn est un **chemin d'import Python** (`module:attribut`), pas un chemin de
> fichier : `.\backend\app.main:app` ne fonctionne pas. Le package `app` doit être importable,
> donc le processus doit tourner depuis `backend/` (c'est ce que fait `--directory backend`).

- API : http://localhost:8000
- Documentation OpenAPI : http://localhost:8000/docs
- Santé : `GET /health` (200 si la base répond, 503 sinon)

## API

| Méthode | Route | Description |
| --- | --- | --- |
| `GET` | `/ingredients` | Liste (`q` : recherche, `aisle`, `limit`, `offset`) |
| `POST` | `/ingredients` | Création (nom unique, insensible à la casse) |
| `GET` / `PATCH` / `DELETE` | `/ingredients/{id}` | Lecture, modification partielle, suppression (409 si utilisé) |
| `GET` | `/recipes` | Recettes visibles (`q`, `tag`, `mine`, `limit`, `offset`) |
| `POST` | `/recipes` | Création avec ses ingrédients |
| `GET` / `PATCH` / `DELETE` | `/recipes/{id}` | Lecture, modification partielle, suppression (409 si planifiée) |

- Toutes les routes sauf `/health` passent par `get_current_user` (utilisateur par défaut du seed).
- **Visibilité** : une recette est visible si j'en suis propriétaire ou si elle est publique
  (`visible_recipes_condition` dans `app/services/recipes.py`, seul endroit où la règle est définie).
  Une recette invisible renvoie 404 ; une recette visible mais d'un autre utilisateur renvoie 403 en
  modification/suppression.
- **PATCH** : seuls les champs envoyés sont modifiés ; `ingredients`, s'il est envoyé, remplace la
  liste complète. `null` n'est accepté que pour `description`.
- **Unités** : à la saisie, `kg`, `cl`, `dl` et `l` sont convertis en `g` / `ml`. Sans unité, l'unité
  par défaut de l'ingrédient est utilisée.
- Erreurs métier : `{"detail": "..."}` avec 403, 404, 409 ou 422.

## Base de données et migrations

Modèles SQLAlchemy dans `app/models`, migrations Alembic dans `alembic/versions`.
L'URL de connexion est lue depuis `DATABASE_URL` (`app/db/config.py`), pas depuis `alembic.ini`.

```bash
# après modification d'un modèle
uv run alembic revision --autogenerate -m "description du changement"
# relire le fichier généré : autogenerate ne détecte pas tout (renommages, données…)
uv run alembic upgrade head
uv run alembic check            # vérifie qu'aucune migration ne manque
```

Les énumérations (`Unit`, `Aisle`, `Visibility`, `Meal`) sont stockées en `VARCHAR(32)` avec une
contrainte `CHECK`, pas en type `ENUM` PostgreSQL : ajouter une valeur = une migration qui met à jour
la contrainte. Les quantités utilisent des **unités normalisées** (`g`, `ml`, `piece`, `tsp`,
`tbsp`, `pinch`) pour pouvoir être additionnées dans la liste de courses.

## Qualité

```bash
uv run ruff check .
uv run ruff format .
uv run pytest
```

Hooks pre-commit (ruff check --fix + ruff format, config dans `.pre-commit-config.yaml` à la racine) :

```bash
uv run pre-commit install           # une fois, après le clone
uv run pre-commit run --all-files   # lancer manuellement
```

Les tests utilisent la base `cuisineausort_test`, créée automatiquement par
`docker/postgres/init/01-create-test-db.sql` à la première initialisation du volume Docker.
Au début de chaque session pytest, son schéma est recréé puis migré (`upgrade` → `downgrade` →
`upgrade`, pour vérifier que les migrations sont réversibles), et chaque test tourne dans une
transaction annulée. `tests/test_migrations.py` échoue si un
modèle a changé sans migration correspondante.
