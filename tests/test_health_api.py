from fastapi.testclient import TestClient

from pi5_scada.app import create_app
from pi5_scada.api import health
from pi5_scada.db import make_engine
from pi5_scada.models import Base


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


def test_health_endpoint_checks_shared_app_engine(monkeypatch) -> None:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    checked_engines = []

    def check_database(engine_to_check) -> bool:
        checked_engines.append(engine_to_check)
        return True

    monkeypatch.setattr(health, "check_database", check_database)
    app = create_app(database_url="sqlite:///:memory:", engine=engine)
    client = TestClient(app)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert checked_engines == [engine]
