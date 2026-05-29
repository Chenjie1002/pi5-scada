from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_serializer


class ProductRecordRead(BaseModel):
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


class ProductRecordList(BaseModel):
    items: list[ProductRecordRead]
    total: int
