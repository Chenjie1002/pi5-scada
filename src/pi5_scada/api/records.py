from fastapi import APIRouter, Request
from sqlalchemy.orm import sessionmaker

from pi5_scada.repositories import ProductRecordRepository
from pi5_scada.schemas import ProductRecordList

router = APIRouter()


@router.get("/records", response_model=ProductRecordList)
def list_records(request: Request) -> ProductRecordList:
    Session = sessionmaker(bind=request.app.state.engine)
    with Session() as session:
        repository = ProductRecordRepository(session)
        return ProductRecordList(
            items=repository.list_records(),
            total=repository.count_records(),
        )
