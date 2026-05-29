from sqlalchemy import select
from sqlalchemy.orm import Session

from pi5_scada.models import ProductRecord


def list_product_records(session: Session, limit: int = 50) -> list[ProductRecord]:
    statement = select(ProductRecord).order_by(ProductRecord.completed_at.desc()).limit(limit)
    return list(session.scalars(statement).all())
