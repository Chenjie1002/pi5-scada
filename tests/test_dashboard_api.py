def test_dashboard_summary_returns_baseline_status(client) -> None:
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == {
        "today_total": 0,
        "today_ok": 0,
        "today_ng": 0,
        "yield_rate": 0.0,
        "current_record_seq": None,
        "plc_status": "not_configured",
        "mcu_status": "not_configured",
    }
