from typing import List, Optional

from fastapi import APIRouter, Cookie, Depends
from sqlalchemy.orm import Session

from app.domains.pipeline.adapter.outbound.persistence.analysis_log_repository_impl import AnalysisLogRepositoryImpl
from app.domains.pipeline.application.request.run_pipeline_request import RunPipelineRequest
from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse
from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse
from app.domains.pipeline.application.usecase.run_pipeline_usecase import RunPipelineUseCase
from app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter import OpenAIAnalyzerAdapter
from app.domains.stock_analyzer.adapter.outbound.in_memory.article_analysis_repository_impl import InMemoryArticleAnalysisRepository
from app.domains.stock_analyzer.application.usecase.get_or_create_analysis_usecase import GetOrCreateAnalysisUseCase
from app.domains.stock_collector.adapter.outbound.external.dart_collector_adapter import DartCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.dart_report_collector_adapter import DartReportCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.news_collector_adapter import NewsCollectorAdapter
from app.domains.stock_collector.adapter.outbound.persistence.raw_article_repository_impl import RawArticleRepositoryImpl
from app.domains.stock_normalizer.application.usecase.normalize_raw_article_usecase import NormalizeRawArticleUseCase
from app.domains.stock_normalizer.infrastructure.repository_registry import normalized_article_repository
from app.domains.watchlist.adapter.outbound.persistence.watchlist_repository_impl import WatchlistRepositoryImpl
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

_settings = get_settings()
_analysis_repository = InMemoryArticleAnalysisRepository()


def _log_to_summary(log) -> StockSummaryResponse:
    return StockSummaryResponse(
        symbol=log.symbol,
        name=log.name,
        summary=log.summary,
        tags=log.tags,
        sentiment=log.sentiment,
        sentiment_score=log.sentiment_score,
        confidence=log.confidence,
        source_type=log.source_type,
    )


@router.post("/run")
async def run_pipeline(
    request: RunPipelineRequest | None = None,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
):
    parsed_account_id = int(account_id) if account_id else None
    usecase = RunPipelineUseCase(
        watchlist_repository=WatchlistRepositoryImpl(db),
        raw_article_repository=RawArticleRepositoryImpl(db),
        collectors=[DartCollectorAdapter(), DartReportCollectorAdapter(), NewsCollectorAdapter()],
        normalize_usecase=NormalizeRawArticleUseCase(normalized_article_repository),
        analysis_usecase=GetOrCreateAnalysisUseCase(
            article_repository=normalized_article_repository,
            analysis_repository=_analysis_repository,
            analyzer_port=OpenAIAnalyzerAdapter(api_key=_settings.openai_api_key, model=_settings.openai_model),
        ),
    )
    selected_symbols = request.symbols if request and request.symbols else None
    result = await usecase.execute(selected_symbols=selected_symbols, account_id=parsed_account_id)

    log_repo = AnalysisLogRepositoryImpl(db)
    log_repo.save_all(result.get("logs", []), account_id=parsed_account_id)

    return {"message": result["message"], "processed": result["processed"]}


@router.get("/summaries", response_model=List[StockSummaryResponse])
async def get_summaries(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
):
    parsed_account_id = int(account_id) if account_id else None
    log_repo = AnalysisLogRepositoryImpl(db)
    logs = log_repo.find_latest_per_symbol(["NEWS"], account_id=parsed_account_id)
    return [_log_to_summary(log) for log in logs]


@router.get("/report-summaries", response_model=List[StockSummaryResponse])
async def get_report_summaries(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
):
    parsed_account_id = int(account_id) if account_id else None
    log_repo = AnalysisLogRepositoryImpl(db)
    logs = log_repo.find_latest_per_symbol(["DISCLOSURE", "REPORT"], account_id=parsed_account_id)
    return [_log_to_summary(log) for log in logs]


@router.get("/logs", response_model=List[AnalysisLogResponse])
async def get_analysis_logs(
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
):
    parsed_account_id = int(account_id) if account_id else None
    log_repo = AnalysisLogRepositoryImpl(db)
    return log_repo.find_recent(limit=50, account_id=parsed_account_id)


async def run_pipeline_job():
    """스케줄러에서 호출되는 파이프라인 자동 실행 함수"""
    import logging
    from app.infrastructure.database.session import SessionLocal
    logger = logging.getLogger(__name__)
    logger.info("[Scheduler] 매일 07:00 파이프라인 자동 실행 시작")
    db = SessionLocal()
    try:
        result = await run_pipeline(db=db)
        logger.info(f"[Scheduler] 파이프라인 완료: {result}")
    except Exception as e:
        logger.error(f"[Scheduler] 파이프라인 실행 실패: {e}")
    finally:
        db.close()
