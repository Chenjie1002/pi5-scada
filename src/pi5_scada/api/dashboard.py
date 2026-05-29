from fastapi import APIRouter

router = APIRouter()


@router.get("/dashboard/summary")
def get_dashboard_summary() -> dict[str, int | float | str | None]:
    return {
        "today_total": 0,
        "today_ok": 0,
        "today_ng": 0,
        "yield_rate": 0.0,
        "current_record_seq": None,
        "plc_status": "not_configured",
        "mcu_status": "not_configured",
    }
