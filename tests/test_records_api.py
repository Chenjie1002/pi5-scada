from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from pi5_scada.app import create_app
from pi5_scada.db import make_engine
from pi5_scada.models import Base, ProductRawData, ProductRecord


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
    plc_snapshot_json: dict | None = None,
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
            plc_snapshot_json=plc_snapshot_json or {},
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        session.expunge(record)
        return record


def add_raw_data(
    engine: Engine,
    *,
    product_record_id: int,
    record_seq: int,
    source_type: str = "mcu",
    capture_seq: int | None = 7,
    status: str = "stored",
    file_path: str | None = "/data/raw/P1001.bin",
    size_bytes: int | None = 2048,
    checksum: str | None = "abc123",
    format_version: str | None = "v1",
    captured_at: datetime | None = None,
    stored_at: datetime | None = None,
    error_message: str | None = None,
) -> ProductRawData:
    Session = sessionmaker(bind=engine)
    with Session() as session:
        raw_data = ProductRawData(
            product_record_id=product_record_id,
            record_seq=record_seq,
            source_type=source_type,
            capture_seq=capture_seq,
            status=status,
            file_path=file_path,
            size_bytes=size_bytes,
            checksum=checksum,
            format_version=format_version,
            captured_at=captured_at,
            stored_at=stored_at,
            error_message=error_message,
        )
        session.add(raw_data)
        session.commit()
        session.refresh(raw_data)
        session.expunge(raw_data)
        return raw_data


def test_fresh_app_initializes_schema_for_records_list(tmp_path: Path) -> None:
    database_url = f"sqlite:///{tmp_path / 'fresh.db'}"
    app = create_app(database_url=database_url)
    client = TestClient(app)

    response = client.get("/api/records")

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


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


def test_list_records_rejects_negative_limit(tmp_path: Path) -> None:
    client, _engine = make_records_client(tmp_path)

    response = client.get("/api/records?limit=-1")

    assert response.status_code == 422


def test_get_record_returns_detail_with_snapshot(tmp_path: Path) -> None:
    client, engine = make_records_client(tmp_path)
    completed_at = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)
    record = add_record(
        engine,
        record_seq=1001,
        product_id="P1001",
        completed_at=completed_at,
        plc_snapshot_json={"db": 12, "result": "OK"},
    )

    response = client.get(f"/api/records/{record.id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": record.id,
        "line_id": "line-1",
        "station_id": "station-1",
        "record_seq": 1001,
        "product_id": "P1001",
        "result": "OK",
        "cycle_time_ms": 1200,
        "completed_at": completed_at.isoformat().replace("+00:00", "Z"),
        "plc_snapshot_json": {"db": 12, "result": "OK"},
    }


def test_get_record_snapshot_returns_snapshot_json(tmp_path: Path) -> None:
    client, engine = make_records_client(tmp_path)
    record = add_record(
        engine,
        record_seq=1001,
        product_id="P1001",
        completed_at=datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc),
        plc_snapshot_json={"line": "line-1", "counter": 1001},
    )

    response = client.get(f"/api/records/{record.id}/snapshot")

    assert response.status_code == 200
    assert response.json() == {"line": "line-1", "counter": 1001}


def test_get_record_raw_data_returns_metadata_rows(tmp_path: Path) -> None:
    client, engine = make_records_client(tmp_path)
    captured_at = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)
    stored_at = datetime(2026, 5, 29, 8, 1, tzinfo=timezone.utc)
    record = add_record(
        engine,
        record_seq=1001,
        product_id="P1001",
        completed_at=datetime(2026, 5, 29, 8, 2, tzinfo=timezone.utc),
    )
    raw_data = add_raw_data(
        engine,
        product_record_id=record.id,
        record_seq=record.record_seq,
        captured_at=captured_at,
        stored_at=stored_at,
    )

    response = client.get(f"/api/records/{record.id}/raw-data")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": raw_data.id,
            "product_record_id": record.id,
            "record_seq": 1001,
            "source_type": "mcu",
            "capture_seq": 7,
            "status": "stored",
            "file_path": "/data/raw/P1001.bin",
            "size_bytes": 2048,
            "checksum": "abc123",
            "format_version": "v1",
            "captured_at": captured_at.isoformat().replace("+00:00", "Z"),
            "stored_at": stored_at.isoformat().replace("+00:00", "Z"),
            "error_message": None,
        }
    ]


def test_get_record_raw_data_returns_empty_list_when_none(tmp_path: Path) -> None:
    client, engine = make_records_client(tmp_path)
    record = add_record(
        engine,
        record_seq=1001,
        product_id="P1001",
        completed_at=datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc),
    )

    response = client.get(f"/api/records/{record.id}/raw-data")

    assert response.status_code == 200
    assert response.json() == []


def test_get_record_returns_404_when_missing(tmp_path: Path) -> None:
    client, _engine = make_records_client(tmp_path)

    response = client.get("/api/records/999")

    assert response.status_code == 404


def test_get_record_snapshot_returns_404_when_record_missing(tmp_path: Path) -> None:
    client, _engine = make_records_client(tmp_path)

    response = client.get("/api/records/999/snapshot")

    assert response.status_code == 404


def test_get_record_raw_data_returns_404_when_record_missing(tmp_path: Path) -> None:
    client, _engine = make_records_client(tmp_path)

    response = client.get("/api/records/999/raw-data")

    assert response.status_code == 404
