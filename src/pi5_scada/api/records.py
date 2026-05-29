from fastapi import APIRouter, Query, Request
from sqlalchemy.orm import sessionmaker

from pi5_scada.repositories import list_product_records
from pi5_scada.schemas import ProductRecordListOut

router = APIRouter()


@router.get("/records", response_model=ProductRecordListOut)
def get_records(request: Request, limit: int = Query(default=50, ge=1, le=500)) -> ProductRecordListOut:
    Session = sessionmaker(bind=request.app.state.engine)
    with Session() as session:
        records = list_product_records(session, limit=limit)
        return ProductRecordListOut(items=records, total=len(records))
