from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.routers import health, ingredients, recipes
from app.db.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    # /health est public (sondes de supervision) ; toutes les autres routes passent par
    # get_current_user
    app.include_router(health.router)
    app.include_router(ingredients.router)
    app.include_router(recipes.router)
    return app


app = create_app()
