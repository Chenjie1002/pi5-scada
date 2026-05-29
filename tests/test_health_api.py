def test_health_endpoint_reports_service_and_database_status(client) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "Pi5 SCADA",
        "database": "ok",
        "plc": "not_configured",
        "mcu": "not_configured",
    }
