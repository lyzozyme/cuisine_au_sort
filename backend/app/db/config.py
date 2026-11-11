from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration de l'application, lue depuis l'environnement et le fichier `.env`."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CuisineAuSort"
    environment: str = "local"

    database_url: str = (
        "postgresql+psycopg://cuisineausort:cuisineausort@localhost:5432/cuisineausort"
    )
    test_database_url: str = (
        "postgresql+psycopg://cuisineausort:cuisineausort@localhost:5432/cuisineausort_test"
    )
    # Délai max (secondes) pour ouvrir une connexion : /health doit échouer vite si la base tombe
    database_connect_timeout: int = 5

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
