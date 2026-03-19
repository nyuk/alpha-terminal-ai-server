from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter import OpenAIAnalyzerAdapter
from app.domains.stock_analyzer.adapter.outbound.in_memory.article_analysis_repository_impl import InMemoryArticleAnalysisRepository
from app.domains.stock_analyzer.application.usecase.get_or_create_analysis_usecase import GetOrCreateAnalysisUseCase
from app.domains.stock_collector.adapter.outbound.external.dart_collector_adapter import DartCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.news_collector_adapter import NewsCollectorAdapter
from app.domains.stock_collector.adapter.outbound.persistence.raw_article_repository_impl import RawArticleRepositoryImpl
from app.domains.stock_collector.application.usecase.collect_articles_usecase import CollectArticlesUseCase
from app.domains.stock_normalizer.application.usecase.normalize_raw_article_usecase import NormalizeRawArticleUseCase
from app.domains.stock_normalizer.application.request.normalize_raw_article_request import NormalizeRawArticleRequest
from app.domains.stock_normalizer.infrastructure.repository_registry import normalized_article_repository
from app.domains.watchlist.adapter.outbound.persistence.watchlist_repository_impl import WatchlistRepositoryImpl
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

_settings = get_settings()
_analysis_repository = InMemoryArticleAnalysisRepository()


# 종목별 최신 요약 결과를 메모리에 보관
class StockSummary(BaseModel):
    symbol: str
    name: str
    summary: str
    tags: list
    sentiment: str
    sentiment_score: float
    confidence: float


_summary_registry: dict[str, StockSummary] = {}


@router.post("/run")
async def run_pipeline(db: Session = Depends(get_db)):
    watchlist_repo = WatchlistRepositoryImpl(db)
    raw_repo = RawArticleRepositoryImpl(db)
    watchlist_items = watchlist_repo.find_all()

    if not watchlist_items:
        return {"message": "관심종목이 없습니다.", "processed": []}

    analyzer_adapter = OpenAIAnalyzerAdapter(api_key=_settings.openai_api_key)
    normalizer_usecase = NormalizeRawArticleUseCase(normalized_article_repository)
    analysis_usecase = GetOrCreateAnalysisUseCase(
        article_repository=normalized_article_repository,
        analysis_repository=_analysis_repository,
        analyzer_port=analyzer_adapter,
    )

    results = []
    for item in watchlist_items:
        symbol = item.symbol
        name = item.name

        # R1 수집
        collectors = [DartCollectorAdapter(), NewsCollectorAdapter()]
        collect_usecase = CollectArticlesUseCase(raw_repo, collectors)
        collected = collect_usecase.execute(symbol)

        # 수집된 기사가 없으면 기존 raw_article에서 가져옴
        raw_articles = raw_repo.find_all(symbol=symbol)
        if not raw_articles:
            results.append({"symbol": symbol, "skipped": True, "reason": "수집된 기사 없음"})
            continue

        best_analysis = None
        for raw in raw_articles[:3]:  # 최대 3건만 분석 (비용 절약)
            try:
                from datetime import datetime as dt
                try:
                    published_at = dt.fromisoformat(str(raw.published_at))
                except Exception:
                    published_at = dt.now()

                # R2 정규화
                normalized = await normalizer_usecase.execute(NormalizeRawArticleRequest(
                    id=str(raw.id),
                    source_type=raw.source_type,
                    source_name=raw.source_name,
                    title=raw.title,
                    body_text=raw.body_text or raw.title,
                    published_at=published_at,
                    symbol=raw.symbol,
                    lang=raw.lang or "en",
                ))

                # R3 분석
                analysis = await analysis_usecase.execute(normalized.id)

                if best_analysis is None or analysis.confidence > best_analysis.confidence:
                    best_analysis = analysis

            except Exception:
                continue

        if best_analysis:
            summary = StockSummary(
                symbol=symbol,
                name=name,
                summary=best_analysis.summary,
                tags=[t.model_dump() for t in best_analysis.tags],
                sentiment=best_analysis.sentiment,
                sentiment_score=best_analysis.sentiment_score,
                confidence=best_analysis.confidence,
            )
            _summary_registry[symbol] = summary
            results.append({"symbol": symbol, "skipped": False, "analysis_count": 1})
        else:
            results.append({"symbol": symbol, "skipped": True, "reason": "분석 실패"})

    return {"message": "파이프라인 완료", "processed": results}


@router.get("/summaries", response_model=List[StockSummary])
async def get_summaries():
    return list(_summary_registry.values())


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
