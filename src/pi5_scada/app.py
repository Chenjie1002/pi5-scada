from fastapi import FastAPI
from sqlalchemy.engine import Engine

from pi5_scada.api.dashboard import router as dashboard_router
from pi5_scada.api.health import router as health_router
from pi5_scada.api.records import router as records_router
from pi5_scada.config import Settings
from pi5_scada.db import initialize_schema, make_engine


def create_app(database_url: str | None = None, engine: Engine | None = None) -> FastAPI:
    settings = Settings()
    if database_url is not None:
        settings.database_url = database_url

    app = FastAPI(title=settings.app_name)
    app.state.settings = settings
    app.state.engine = engine if engine is not None else make_engine(settings.database_url)
    initialize_schema(app.state.engine)
    app.include_router(health_router, prefix="/api")
    app.include_router(records_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/api")
    return app
