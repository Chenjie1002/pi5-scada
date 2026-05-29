from fastapi import FastAPI

from pi5_scada.api.health import router as health_router
from pi5_scada.config import Settings


def create_app(database_url: str | None = None) -> FastAPI:
    settings = Settings()
    if database_url is not None:
        settings.database_url = database_url

    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.include_router(health_router, prefix="/api")
    return app
