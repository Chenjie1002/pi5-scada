from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from pi5_scada.app import create_app
from pi5_scada.db import make_engine
from pi5_scada.models import Base, ProductRecord


def make_records_client(tmp_path: Path) -> tuple[TestClient, Engine]:
    database_url = f"sqlite:///{tmp_path / 'records.db'}"
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)
    app = create_app(database_url="sqlite:///:memory:", engine=engine)
    return TestClient(app), engine


def add_record(
    engine: Engine,
    *,
    line_id: str = "line-1",
    station_id: str = "station-1",
    record_seq: int,
    product_id: str,
    result: str = "OK",
    cycle_time_ms: int | None = 1200,
    completed_at: datetime,
) -> ProductRecord:
    Session = sessionmaker(bind=engine)
    with Session() as session:
        record = ProductRecord(
            line_id=line_id,
            station_id=station_id,
            record_seq=record_seq,
            product_id=product_id,
            result=result,
            cycle_time_ms=cycle_time_ms,
            completed_at=completed_at,
            plc_snapshot_json={},
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        session.expunge(record)
        return record


def test_list_records_returns_items_and_total_from_shared_engine(tmp_path: Path) -> None:
    client, engine = make_records_client(tmp_path)
    completed_at = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)
    record = add_record(
        engine,
        record_seq=1001,
        product_id="P1001",
        result="NG",
        cycle_time_ms=1350,
        completed_at=completed_at,
    )

    response = client.get("/api/records")

    assert response.status_code == 200
    assert response.json() == {
        "items": [
            {
                "id": record.id,
                "line_id": "line-1",
                "station_id": "station-1",
                "record_seq": 1001,
                "product_id": "P1001",
                "result": "NG",
                "cycle_time_ms": 1350,
                "completed_at": completed_at.isoformat().replace("+00:00", "Z"),
            }
        ],
        "total": 1,
    }


def test_list_records_orders_by_completed_at_descending(tmp_path: Path) -> None:
    client, engine = make_records_client(tmp_path)
    older = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)
    newer = datetime(2026, 5, 29, 8, 5, tzinfo=timezone.utc)
    add_record(engine, record_seq=1001, product_id="P1001", completed_at=older)
    add_record(engine, record_seq=1002, product_id="P1002", completed_at=newer)

    response = client.get("/api/records")

    assert response.status_code == 200
    assert [item["record_seq"] for item in response.json()["items"]] == [1002, 1001]
    assert response.json()["total"] == 2


def test_list_records_applies_limit_to_items_and_total(tmp_path: Path) -> None:
    client, engine = make_records_client(tmp_path)
    older = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)
    newer = datetime(2026, 5, 29, 8, 5, tzinfo=timezone.utc)
    add_record(engine, record_seq=1001, product_id="P1001", completed_at=older)
    add_record(engine, record_seq=1002, product_id="P1002", completed_at=newer)

    response = client.get("/api/records?limit=1")

    assert response.status_code == 200
    assert [item["record_seq"] for item in response.json()["items"]] == [1002]
    assert response.json()["total"] == 1
