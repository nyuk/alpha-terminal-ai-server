import asyncio
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.domains.pipeline.adapter.outbound.persistence.analysis_log_repository_impl import AnalysisLogRepositoryImpl
from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse
from app.domains.stock.adapter.outbound.external.dart_corp_code_adapter import DartCorpCodeAdapter
from app.domains.stock.adapter.outbound.external.krx_market_adapter import KrxMarketAdapter
from app.domains.stock.adapter.outbound.persistence.stock_repository_impl import StockRepositoryImpl
from app.domains.stock.application.response.daily_returns_heatmap_response import DailyReturnsHeatmapResponse
from app.domains.stock.application.response.stock_response import StockResponse
from app.domains.stock.application.usecase.daily_returns_heatmap_usecase import DailyReturnsHeatmapUseCase
from app.domains.stock.application.usecase.search_stock_usecase import SearchStockUseCase
from app.domains.stock.application.usecase.sync_corp_code_usecase import SyncCorpCodeUseCase
from app.domains.stock.application.usecase.sync_market_usecase import SyncMarketUseCase
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db
from sqlalchemy.orm import Session


class StockDetailResponse(BaseModel):
    symbol: str
    name: str
    market: Optional[str] = None
    analysis_logs: List[AnalysisLogResponse] = []


router = APIRouter(prefix="/stocks", tags=["stocks"])

logger = logging.getLogger(__name__)

_dart_adapter = DartCorpCodeAdapter()
_krx_market_adapter = KrxMarketAdapter()


@router.get("/search", response_model=List[StockResponse])
async def search_stocks(
    q: str = Query(min_length=1),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    usecase = SearchStockUseCase(StockRepositoryImpl(db), settings.finnhub_api_key)
    return usecase.execute(q)


@router.get("/daily-returns-heatmap", response_model=DailyReturnsHeatmapResponse)
async def daily_returns_heatmap(
    symbols: str = Query(..., min_length=1, description="콤마로 구분된 종목코드 (예: 005930,AAPL)"),
    weeks: int = Query(6, ge=1, le=13),
    db: Session = Depends(get_db),
):
    """BL-BE-13/14: 일별 등락 bucket 배치 조회 (KRX=data.go.kr, US=Twelve Data)."""
    sym_list = [s.strip() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        raise HTTPException(status_code=400, detail="유효한 symbols가 없습니다.")
    settings = get_settings()
    usecase = DailyReturnsHeatmapUseCase(
        StockRepositoryImpl(db),
        settings.data_go_kr_service_key,
        settings.twelve_data_api_key,
        settings.alpha_vantage_api_key,
        heatmap_redis_cache_enabled=settings.heatmap_redis_cache_enabled,
    )
    return await asyncio.to_thread(usecase.execute, sym_list, weeks)


@router.get("/sync", response_model=dict)
async def sync_corp_codes(db: Session = Depends(get_db)):
    """DART 전체 기업코드를 DB에 동기화한다 (최초 1회 또는 갱신 필요 시)"""
    try:
        usecase = SyncCorpCodeUseCase(_dart_adapter, StockRepositoryImpl(db))
        count = await asyncio.to_thread(usecase.execute)
        return {"synced": count}
    except Exception as e:
        logger.error(f"[SyncCorpCode] 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")


@router.get("/sync-market", response_model=dict)
async def sync_market(db: Session = Depends(get_db)):
    """KRX KIND에서 KOSPI/KOSDAQ/KONEX 시장구분을 가져와 DB에 업데이트한다"""
    try:
        usecase = SyncMarketUseCase(_krx_market_adapter, StockRepositoryImpl(db))
        count = await asyncio.to_thread(usecase.execute)
        return {"updated": count}
    except Exception as e:
        logger.error(f"[SyncMarket] 실패: {e}")
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")


@router.get("/{symbol}", response_model=StockDetailResponse)
def get_stock_detail(symbol: str, db: Session = Depends(get_db)):
    """종목 상세 — 기본 정보 + AI 분석 이력 최근 20건."""
    symbol = symbol.strip().upper()
    stock = StockRepositoryImpl(db).find_by_symbol(symbol)
    if not stock:
        raise HTTPException(status_code=404, detail="종목을 찾을 수 없습니다.")
    logs = AnalysisLogRepositoryImpl(db).find_by_symbol(symbol, limit=20)
    return StockDetailResponse(
        symbol=stock.symbol,
        name=stock.name,
        market=stock.market,
        analysis_logs=logs,
    )
