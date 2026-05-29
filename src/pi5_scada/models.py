from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, event, func
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


@event.listens_for(Session, "before_commit")
def _keep_attributes_loaded_after_commit(session: Session) -> None:
    session.expire_on_commit = False


class ProductRecord(Base):
    __tablename__ = "product_records"
    __table_args__ = (
        UniqueConstraint("line_id", "station_id", "record_seq", name="uq_product_trace_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    line_id: Mapped[str] = mapped_column(String(64), index=True)
    station_id: Mapped[str] = mapped_column(String(64), index=True)
    record_seq: Mapped[int] = mapped_column(Integer, index=True)
    product_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    result: Mapped[str] = mapped_column(String(16), index=True)
    cycle_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    plc_snapshot_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProductRawData(Base):
    __tablename__ = "product_raw_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_record_id: Mapped[int] = mapped_column(ForeignKey("product_records.id"), index=True)
    record_seq: Mapped[int] = mapped_column(Integer, index=True)
    source_type: Mapped[str] = mapped_column(String(32))
    capture_seq: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str | None] = mapped_column(String(128), nullable=True)
    format_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    stored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(1024), nullable=True)


class ProductionMetric(Base):
    __tablename__ = "production_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    bucket_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    bucket_seconds: Mapped[int] = mapped_column(Integer)
    line_id: Mapped[str] = mapped_column(String(64), index=True)
    station_id: Mapped[str] = mapped_column(String(64), index=True)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    ok_count: Mapped[int] = mapped_column(Integer, default=0)
    ng_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_cycle_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    planned_count: Mapped[int | None] = mapped_column(Integer, nullable=True)


class SystemConfig(Base):
    __tablename__ = "system_config"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CollectorEvent(Base):
    __tablename__ = "collector_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    event_code: Mapped[str] = mapped_column(String(64), index=True)
    message: Mapped[str] = mapped_column(String(512))
    detail_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
