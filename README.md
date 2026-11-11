## Cuisine au sort

Interface d'enregistrements de recettes et génération de listes de courses.

### Démarrage rapide (depuis la racine)

```bash
docker compose up -d db
cp backend/.env.example backend/.env
uv run --directory backend uvicorn app.main:app --reload
```

Détails : [backend/README.md](backend/README.md).
