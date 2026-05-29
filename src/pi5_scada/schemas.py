from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


class ProductRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    line_id: str
    station_id: str
    record_seq: int
    product_id: str | None
    result: str
    cycle_time_ms: int | None
    completed_at: datetime

    @field_serializer("completed_at")
    def serialize_completed_at(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")


class ProductRecordListOut(BaseModel):
    items: list[ProductRecordOut]
    total: int


class ProductRecordDetailOut(ProductRecordOut):
    plc_snapshot_json: dict


class ProductRawDataOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_record_id: int
    record_seq: int
    source_type: str
    capture_seq: int | None
    status: str
    file_path: str | None
    size_bytes: int | None
    checksum: str | None
    format_version: str | None
    captured_at: datetime | None
    stored_at: datetime | None
    error_message: str | None

    @field_serializer("captured_at", "stored_at")
    def serialize_optional_datetime(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")
