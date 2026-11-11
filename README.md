## Cuisine au sort

Interface d'enregistrements de recettes et génération de listes de courses.

### Démarrage rapide (depuis la racine)

```bash
docker compose up -d db
cp backend/.env.example backend/.env
uv run --directory backend alembic upgrade head
uv run --directory backend python -m app.db.seed
uv run --directory backend uvicorn app.main:app --reload   # API sur http://127.0.0.1:8000

# dans un second terminal
cd frontend && npm install && npm run dev                  # interface sur http://localhost:5173
```

Détails : [backend/README.md](backend/README.md), [frontend/README.md](frontend/README.md).
