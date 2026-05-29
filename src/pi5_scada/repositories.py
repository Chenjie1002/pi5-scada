from sqlalchemy import select
from sqlalchemy.orm import Session

from pi5_scada.models import ProductRawData, ProductRecord


def list_product_records(session: Session, limit: int = 50) -> list[ProductRecord]:
    statement = select(ProductRecord).order_by(ProductRecord.completed_at.desc()).limit(limit)
    return list(session.scalars(statement).all())


def get_product_record(session: Session, record_id: int) -> ProductRecord | None:
    return session.get(ProductRecord, record_id)


def list_product_raw_data(session: Session, product_record_id: int) -> list[ProductRawData]:
    statement = (
        select(ProductRawData)
        .where(ProductRawData.product_record_id == product_record_id)
        .order_by(ProductRawData.id.asc())
    )
    return list(session.scalars(statement).all())
