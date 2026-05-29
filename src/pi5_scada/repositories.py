from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pi5_scada.models import ProductRecord


class ProductRecordRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_records(self) -> list[ProductRecord]:
        statement = select(ProductRecord).order_by(ProductRecord.completed_at.desc())
        return list(self.session.scalars(statement).all())

    def count_records(self) -> int:
        statement = select(func.count()).select_from(ProductRecord)
        return self.session.scalar(statement) or 0
