import pytest
from fastapi.testclient import TestClient

from pi5_scada.app import create_app
from pi5_scada.db import make_engine
from pi5_scada.models import Base


@pytest.fixture()
def client() -> TestClient:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app = create_app(database_url="sqlite:///:memory:", engine=engine)
    return TestClient(app)
