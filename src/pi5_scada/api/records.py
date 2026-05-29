from fastapi import APIRouter, HTTPException, Query, Request
from sqlalchemy.orm import sessionmaker

from pi5_scada.repositories import (
    get_product_record,
    list_product_raw_data,
    list_product_records,
)
from pi5_scada.schemas import (
    ProductRawDataOut,
    ProductRecordDetailOut,
    ProductRecordListOut,
)

router = APIRouter()


@router.get("/records", response_model=ProductRecordListOut)
def get_records(request: Request, limit: int = Query(default=50, ge=1, le=500)) -> ProductRecordListOut:
    Session = sessionmaker(bind=request.app.state.engine)
    with Session() as session:
        records = list_product_records(session, limit=limit)
        return ProductRecordListOut(items=records, total=len(records))


@router.get("/records/{record_id}", response_model=ProductRecordDetailOut)
def get_record(request: Request, record_id: int) -> ProductRecordDetailOut:
    Session = sessionmaker(bind=request.app.state.engine)
    with Session() as session:
        record = get_product_record(session, record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Product record not found")
        return ProductRecordDetailOut.model_validate(record)


@router.get("/records/{record_id}/snapshot", response_model=dict)
def get_record_snapshot(request: Request, record_id: int) -> dict:
    Session = sessionmaker(bind=request.app.state.engine)
    with Session() as session:
        record = get_product_record(session, record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Product record not found")
        return record.plc_snapshot_json


@router.get("/records/{record_id}/raw-data", response_model=list[ProductRawDataOut])
def get_record_raw_data(request: Request, record_id: int) -> list[ProductRawDataOut]:
    Session = sessionmaker(bind=request.app.state.engine)
    with Session() as session:
        record = get_product_record(session, record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Product record not found")
        return list_product_raw_data(session, product_record_id=record.id)
