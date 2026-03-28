from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.domains.pipeline.adapter.outbound.persistence.analysis_log_repository_impl import AnalysisLogRepositoryImpl
from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/public", tags=["public"])

PUBLIC_SYMBOLS = ["005930", "000660"]  # 삼성전자, SK하이닉스


@router.get("/summaries", response_model=List[StockSummaryResponse])
async def get_public_summaries(
    symbols: str = ",".join(PUBLIC_SYMBOLS),
    db: Session = Depends(get_db),
):
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    log_repo = AnalysisLogRepositoryImpl(db)
    logs = log_repo.find_latest_by_symbols(symbol_list)
    return [
        StockSummaryResponse(
            symbol=log.symbol,
            name=log.name,
            summary=log.summary,
            tags=log.tags,
            sentiment=log.sentiment,
            sentiment_score=log.sentiment_score,
            confidence=log.confidence,
            source_type=log.source_type,
            url=log.url,
            analyzed_at=log.analyzed_at,
        )
        for log in logs
    ]
