import asyncio
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.domains.stock.adapter.outbound.external.dart_corp_code_adapter import DartCorpCodeAdapter
from app.domains.stock.adapter.outbound.persistence.stock_repository_impl import StockRepositoryImpl
from app.domains.stock.application.response.stock_response import StockResponse
from app.domains.stock.application.usecase.search_stock_usecase import SearchStockUseCase
from app.domains.stock.application.usecase.sync_corp_code_usecase import SyncCorpCodeUseCase
from app.infrastructure.database.session import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/stocks", tags=["stocks"])

logger = logging.getLogger(__name__)

_dart_adapter = DartCorpCodeAdapter()


@router.get("/search", response_model=List[StockResponse])
async def search_stocks(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
):
    usecase = SearchStockUseCase(StockRepositoryImpl(db))
    return usecase.execute(q)


@router.get("/sync", response_model=dict)
async def sync_corp_codes(db: Session = Depends(get_db)):
    """DART 전체 기업코드를 DB에 동기화한다 (최초 1회 또는 갱신 필요 시)"""
    try:
        usecase = SyncCorpCodeUseCase(_dart_adapter, StockRepositoryImpl(db))
        count = await asyncio.to_thread(usecase.execute)
        return {"synced": count}
    except Exception as e:
        logger.error(f"[SyncCorpCode] 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))
