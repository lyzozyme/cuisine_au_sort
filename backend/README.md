# Backend CuisineAuSort

API FastAPI + SQLAlchemy 2.x + PostgreSQL, dépendances gérées avec [uv](https://docs.astral.sh/uv/).

## Démarrage

```bash
# depuis la racine du dépôt : lancer PostgreSQL
docker compose up -d db

# depuis backend/
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```

- API : http://localhost:8000
- Documentation OpenAPI : http://localhost:8000/docs
- Santé : `GET /health` (200 si la base répond, 503 sinon)

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
