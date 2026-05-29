from fastapi import APIRouter, Request

from pi5_scada.db import check_database

router = APIRouter()


@router.get("/health")
def get_health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    check_database(request.app.state.engine)
    return {
        "status": "ok",
        "app": settings.app_name,
        "database": "ok",
        "plc": "not_configured",
        "mcu": "not_configured",
    }
