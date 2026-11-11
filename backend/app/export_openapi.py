"""Écrit le schéma OpenAPI de l'API dans un fichier, sans lancer le serveur ni la base.

Usage (depuis backend/) :
    uv run python -m app.export_openapi ../frontend/openapi.json

Utilisé par le frontend (`npm run api:generate`) pour générer son client typé.
"""

import json
import sys
from pathlib import Path

from app.main import app


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage : python -m app.export_openapi <fichier.json>")
    output = Path(sys.argv[1])
    output.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Schéma OpenAPI écrit dans {output.resolve()}")


if __name__ == "__main__":
    main()
