import asyncio
import logging
from datetime import datetime
from typing import Optional

from app.domains.pipeline.application.response.analysis_log_response import AnalysisLogResponse
from app.domains.pipeline.application.response.stock_summary_response import StockSummaryResponse
from app.domains.stock_analyzer.application.usecase.get_or_create_analysis_usecase import GetOrCreateAnalysisUseCase
from app.domains.stock_collector.application.usecase.collect_articles_usecase import CollectArticlesUseCase
from app.domains.stock_normalizer.application.request.normalize_raw_article_request import NormalizeRawArticleRequest
from app.domains.stock_normalizer.application.usecase.normalize_raw_article_usecase import NormalizeRawArticleUseCase

logger = logging.getLogger(__name__)


class RunPipelineUseCase:
    def __init__(
        self,
        watchlist_repository,
        raw_article_repository,
        collectors: list,
        normalize_usecase: NormalizeRawArticleUseCase,
        analysis_usecase: GetOrCreateAnalysisUseCase,
    ):
        self._watchlist_repository = watchlist_repository
        self._raw_article_repository = raw_article_repository
        self._collectors = collectors
        self._normalize_usecase = normalize_usecase
        self._analysis_usecase = analysis_usecase

    async def execute(self, selected_symbols: Optional[list[str]] = None, account_id: Optional[int] = None) -> dict:
        watchlist_items = self._watchlist_repository.find_all(account_id=account_id)
        if not watchlist_items:
            return {"message": "관심종목이 없습니다.", "processed": [], "summaries": [], "logs": []}

        if selected_symbols:
            selected_set = {symbol.upper() for symbol in selected_symbols}
            watchlist_items = [item for item in watchlist_items if item.symbol.upper() in selected_set]
            if not watchlist_items:
                return {"message": "선택한 관심종목이 없습니다.", "processed": [], "summaries": [], "logs": []}

        results = []
        summaries = []
        logs = []

        for item in watchlist_items:
            symbol = item.symbol
            name = item.name

            collect_usecase = CollectArticlesUseCase(self._raw_article_repository, self._collectors)
            await asyncio.to_thread(collect_usecase.execute, symbol)

            raw_articles = self._raw_article_repository.find_all(symbol=symbol)
            if not raw_articles:
                results.append({"symbol": symbol, "skipped": True, "reason": "수집된 기사 없음"})
                continue

            best_analysis = None
            for raw in raw_articles[:3]:
                try:
                    try:
                        published_at = datetime.fromisoformat(str(raw.published_at))
                    except Exception:
                        published_at = datetime.now()

                    normalized = await self._normalize_usecase.execute(NormalizeRawArticleRequest(
                        id=str(raw.id),
                        source_type=raw.source_type,
                        source_name=raw.source_name,
                        title=raw.title,
                        body_text=raw.body_text or raw.title,
                        published_at=published_at,
                        symbol=raw.symbol,
                        lang=raw.lang or "en",
                    ))

                    analysis = await self._analysis_usecase.execute(normalized.id)

                    if best_analysis is None or analysis.confidence > best_analysis.confidence:
                        best_analysis = analysis

                except Exception as e:
                    logger.warning(f"[Pipeline] {symbol} 기사 분석 실패: {e}")
                    continue

            if best_analysis:
                tags = [t.label for t in best_analysis.tags]
                summary = StockSummaryResponse(
                    symbol=symbol,
                    name=name,
                    summary=best_analysis.summary,
                    tags=tags,
                    sentiment=best_analysis.sentiment,
                    sentiment_score=best_analysis.sentiment_score,
                    confidence=best_analysis.confidence,
                )
                summaries.append(summary)
                logs.append(AnalysisLogResponse(
                    analyzed_at=datetime.now(),
                    symbol=symbol,
                    name=name,
                    summary=best_analysis.summary,
                    tags=tags,
                    sentiment=best_analysis.sentiment,
                    sentiment_score=best_analysis.sentiment_score,
                    confidence=best_analysis.confidence,
                ))
                results.append({"symbol": symbol, "skipped": False, "analysis_count": 1})
            else:
                results.append({"symbol": symbol, "skipped": True, "reason": "분석 실패"})

        return {"message": "파이프라인 완료", "processed": results, "summaries": summaries, "logs": logs}
