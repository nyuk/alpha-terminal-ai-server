import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, Cookie, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.domains.pipeline.adapter.outbound.persistence.analysis_log_repository_impl import AnalysisLogRepositoryImpl
from app.domains.pipeline.adapter.outbound.state.factory import get_progress_store, get_summary_registry
from app.domains.pipeline.application.request.run_pipeline_request import ArticleMode, RunPipelineRequest
from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse
from app.domains.pipeline.application.response.run_pipeline_result import RunPipelineResponse
from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse
from app.domains.pipeline.application.usecase.run_pipeline_usecase import RunPipelineUseCase
from app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter import OpenAIAnalyzerAdapter
from app.domains.stock_analyzer.adapter.outbound.in_memory.article_analysis_repository_impl import InMemoryArticleAnalysisRepository
from app.domains.stock_analyzer.application.usecase.get_or_create_analysis_usecase import GetOrCreateAnalysisUseCase
from app.domains.stock_collector.adapter.outbound.external.dart_collector_adapter import DartCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.dart_report_collector_adapter import DartReportCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.finnhub_collector_adapter import FinnhubCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.naver_news_collector_adapter import NaverNewsCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.news_collector_adapter import NewsCollectorAdapter
from app.domains.stock.adapter.outbound.persistence.stock_repository_impl import StockRepositoryImpl
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
        url=getattr(log, "url", None),
        analyzed_at=getattr(log, "analyzed_at", None),
        article_published_at=getattr(log, "article_published_at", None),
        source_name=getattr(log, "source_name", None),
    )


def _build_usecase(db: Session) -> RunPipelineUseCase:
    analyzer_port = OpenAIAnalyzerAdapter(api_key=_settings.openai_api_key, model=_settings.openai_model)
    return RunPipelineUseCase(
        watchlist_repository=WatchlistRepositoryImpl(db),
        raw_article_repository=RawArticleRepositoryImpl(db),
        stock_repository=StockRepositoryImpl(db),
        collectors=[
            DartCollectorAdapter(),
            DartReportCollectorAdapter(),
            NewsCollectorAdapter(),
            FinnhubCollectorAdapter(),
            NaverNewsCollectorAdapter(),
        ],
        normalize_usecase=NormalizeRawArticleUseCase(normalized_article_repository),
        analysis_usecase=GetOrCreateAnalysisUseCase(
            article_repository=normalized_article_repository,
            analysis_repository=_analysis_repository,
            analyzer_port=analyzer_port,
        ),
        analyzer_port=analyzer_port,
    )


@router.post("/run", response_model=RunPipelineResponse)
async def run_pipeline(
    request: RunPipelineRequest | None = None,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
):
    parsed_account_id = int(account_id) if account_id else None
    selected_symbols = request.symbols if request and request.symbols else None
    article_mode = request.article_mode if request else ArticleMode.LATEST_3
    result = await _build_usecase(db).execute(
        selected_symbols=selected_symbols,
        account_id=parsed_account_id,
        article_mode=article_mode,
    )

    get_summary_registry().put_all(parsed_account_id, result.summaries)

    log_repo = AnalysisLogRepositoryImpl(db)
    log_repo.save_all(result.logs, account_id=parsed_account_id)

    # BL-BE-86: RunPipelineResponse DTO 로 명시적 반환
    return RunPipelineResponse(message=result.message, processed=result.processed)


@router.post("/run-stream")
async def run_pipeline_stream(
    request: RunPipelineRequest | None = None,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
):
    if account_id is None:
        return Response(status_code=401)

    parsed_account_id = int(account_id)
    selected_symbols = request.symbols if request and request.symbols else None
    article_mode = request.article_mode if request else ArticleMode.LATEST_3

    async def event_generator() -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[Optional[dict]] = asyncio.Queue()

        async def on_event(event: dict) -> None:
            await queue.put(event)

        async def run():
            # 클라이언트 연결 해제 시에도 세션이 살아있도록 독립 세션 사용
            from app.infrastructure.database.session import SessionLocal
            local_db = SessionLocal()
            try:
                result = await _build_usecase(local_db).execute(
                    selected_symbols=selected_symbols,
                    account_id=parsed_account_id,
                    on_event=on_event,
                    article_mode=article_mode,
                )
                get_summary_registry().put_all(parsed_account_id, result.summaries)
                log_repo = AnalysisLogRepositoryImpl(local_db)
                log_repo.save_all(result.logs, account_id=parsed_account_id)
                await queue.put({
                    "type": "done",
                    "at": datetime.now(timezone.utc).isoformat(),
                    "message": result.message,
                    "processed": result.processed,
                })
            except Exception as e:
                await queue.put({"type": "error", "at": datetime.now(timezone.utc).isoformat(), "message": str(e)})
            finally:
                local_db.close()
                await queue.put(None)

        task = asyncio.create_task(run())

        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

        await task

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/progress")
async def get_progress(account_id: Optional[str] = Cookie(default=None)):
    parsed_account_id = int(account_id) if account_id else None
    messages = get_progress_store().read_all(parsed_account_id)
    done = bool(messages) and messages[-1].startswith("✅")
    return {"messages": messages, "done": done}


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
    """스케줄러에서 호출되는 파이프라인 자동 실행 함수.

    HTTP 라우트 핸들러(`run_pipeline`)를 직접 호출하지 않고 `RunPipelineUseCase` 를 바로 실행한다.
    이로써 HTTP 계층(쿠키/의존성)과 작업 계층을 분리하고, 모든 사용자(account_id=None, 즉 전역 관심종목)
    범위에서 동작하도록 한다.
    """
    import logging
    from app.infrastructure.database.session import SessionLocal
    logger = logging.getLogger(__name__)
    logger.info("[Scheduler] 매일 07:00 파이프라인 자동 실행 시작")
    db = SessionLocal()
    try:
        result = await _build_usecase(db).execute(article_mode=ArticleMode.LATEST_3)
        get_summary_registry().put_all(None, result.summaries)
        log_repo = AnalysisLogRepositoryImpl(db)
        log_repo.save_all(result.logs, account_id=None)
        logger.info(f"[Scheduler] 파이프라인 완료: {result.message} / processed={len(result.processed)}")
    except Exception as e:
        db.rollback()
        logger.error(f"[Scheduler] 파이프라인 실행 실패: {e}")
    finally:
        db.close()
