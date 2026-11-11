from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, résolu indépendamment du répertoire courant (uvicorn/pytest lancés depuis la racine)
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    """Configuration de l'application, lue depuis l'environnement et le fichier `.env`."""

    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CuisineAuSort"
    environment: str = "local"

    database_url: str = (
        "postgresql+psycopg://cuisineausort:cuisineausort@127.0.0.1:5432/cuisineausort"
    )
    test_database_url: str = (
        "postgresql+psycopg://cuisineausort:cuisineausort@127.0.0.1:5432/cuisineausort_test"
    )
    # Délai max (secondes) pour ouvrir une connexion : /health doit échouer vite si la base tombe
    database_connect_timeout: int = 5

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # Utilisateur unique créé par le seed, renvoyé par get_current_user tant qu'il n'y a pas d'auth
    default_user_email: str = "default@cuisineausort.local"
    default_user_display_name: str = "Utilisateur par défaut"


@lru_cache
def get_settings() -> Settings:
    return Settings()
