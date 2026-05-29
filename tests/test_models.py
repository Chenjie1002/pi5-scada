from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pi5_scada.models import Base, ProductRecord, ProductRawData


def test_product_record_unique_trace_key() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        completed_at = datetime(2026, 5, 29, 8, 0, tzinfo=timezone.utc)
        record = ProductRecord(
            line_id="line-1",
            station_id="station-1",
            record_seq=1001,
            product_id="P1001",
            result="OK",
            cycle_time_ms=1200,
            completed_at=completed_at,
            plc_snapshot_json={"pressure": 1.23},
        )
        session.add(record)
        session.commit()

        loaded = session.query(ProductRecord).one()

    assert loaded.line_id == "line-1"
    assert loaded.station_id == "station-1"
    assert loaded.record_seq == 1001
    assert loaded.plc_snapshot_json == {"pressure": 1.23}


def test_raw_data_can_reference_product_record() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        record = ProductRecord(
            line_id="line-1",
            station_id="station-1",
            record_seq=1002,
            product_id="P1002",
            result="NG",
            cycle_time_ms=1300,
            completed_at=datetime(2026, 5, 29, 8, 1, tzinfo=timezone.utc),
            plc_snapshot_json={"temperature": 42.0},
        )
        session.add(record)
        session.flush()
        record_id = record.id
        raw = ProductRawData(
            product_record_id=record_id,
            record_seq=1002,
            source_type="mcu",
            capture_seq=501,
            status="pending",
        )
        session.add(raw)
        session.commit()

        loaded = session.query(ProductRawData).one()

    assert loaded.product_record_id == record_id
    assert loaded.record_seq == 1002
    assert loaded.status == "pending"
