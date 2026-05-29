import pytest
from fastapi.testclient import TestClient

from pi5_scada.app import create_app


@pytest.fixture()
def client() -> TestClient:
    app = create_app(database_url="sqlite:///:memory:")
    return TestClient(app)
