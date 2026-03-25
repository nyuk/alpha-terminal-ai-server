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

NEWS_SOURCE_TYPES = {"NEWS"}
REPORT_SOURCE_TYPES = {"DISCLOSURE", "REPORT"}


class RunPipelineUseCase:
    def __init__(
        self,
        watchlist_repository,
        raw_article_repository,
        collectors: list,
        normalize_usecase: NormalizeRawArticleUseCase,
        analysis_usecase: GetOrCreateAnalysisUseCase,
        on_progress=None,
        stock_repository=None,
    ):
        self._watchlist_repository = watchlist_repository
        self._raw_article_repository = raw_article_repository
        self._collectors = collectors
        self._normalize_usecase = normalize_usecase
        self._analysis_usecase = analysis_usecase
        self._on_progress = on_progress
        self._stock_repository = stock_repository

    def _progress(self, msg: str):
        if self._on_progress:
            self._on_progress(msg)

    async def execute(self, selected_symbols: Optional[list[str]] = None, account_id: Optional[int] = None) -> dict:
        watchlist_items = self._watchlist_repository.find_all(account_id=account_id)
        if not watchlist_items:
            return {"message": "관심종목이 없습니다.", "processed": [], "summaries": [], "report_summaries": [], "logs": []}

        if selected_symbols:
            selected_set = {symbol.upper() for symbol in selected_symbols}
            watchlist_items = [item for item in watchlist_items if item.symbol.upper() in selected_set]
            if not watchlist_items:
                return {"message": "선택한 관심종목이 없습니다.", "processed": [], "summaries": [], "report_summaries": [], "logs": []}

        total = len(watchlist_items)
        self._progress(f"관심종목 {total}개 파이프라인 시작")

        # Phase 1: 수집 (순차 — DB 세션 공유)
        no_article_symbols = []
        symbol_data: dict[str, tuple] = {}  # symbol → (name, news_articles, report_articles)

        for idx, item in enumerate(watchlist_items, 1):
            symbol = item.symbol
            name = item.name
            self._progress(f"[{idx}/{total}] {name}({symbol}) 기사 수집 중...")
            try:
                collect_usecase = CollectArticlesUseCase(self._raw_article_repository, self._collectors, self._stock_repository)
                await asyncio.to_thread(collect_usecase.execute, symbol)
            except Exception as e:
                logger.error(f"[Pipeline] {name}({symbol}) 수집 중 오류: {e}")
                self._progress(f"[{idx}/{total}] {name}({symbol}) 수집 오류 — 건너뜁니다")
                no_article_symbols.append(symbol)
                continue

            raw_articles = self._raw_article_repository.find_all(symbol=symbol)
            if not raw_articles:
                self._progress(f"[{idx}/{total}] {name} — 수집된 기사 없음, 건너뜀")
                no_article_symbols.append(symbol)
                continue

            news_articles = [r for r in raw_articles if r.source_type in NEWS_SOURCE_TYPES]
            report_articles = [r for r in raw_articles if r.source_type in REPORT_SOURCE_TYPES]
            self._progress(f"[{idx}/{total}] {name} — 뉴스 {len(news_articles)}건, 공시 {len(report_articles)}건 수집 완료")
            symbol_data[symbol] = (item.name, news_articles[:1], report_articles[:1])

        self._progress(f"수집 완료. {len(symbol_data)}개 종목 AI 분석 시작...")

        # Phase 2: AI 분석 (병렬 — DB 미사용)
        async def analyze_pair(symbol: str, name: str, news_arts, report_arts):
            self._progress(f"{name}({symbol}) AI 분석 중...")
            news_best, report_best = await asyncio.gather(
                self._analyze_best(news_arts, symbol),
                self._analyze_best(report_arts, symbol),
            )
            self._progress(f"{name}({symbol}) 분석 완료")
            return symbol, name, news_best, report_best

        analysis_results = await asyncio.gather(*[
            analyze_pair(symbol, name, news, report)
            for symbol, (name, news, report) in symbol_data.items()
        ])

        # Phase 3: 결과 집계
        results = [{"symbol": s, "skipped": True, "reason": "수집된 기사 없음"} for s in no_article_symbols]
        summaries = []
        report_summaries = []
        logs = []

        for symbol, name, news_best, report_best in analysis_results:
            if news_best:
                analysis, source_type, url = news_best
                tags = [t.label for t in analysis.tags]
                summaries.append(StockSummaryResponse(
                    symbol=symbol, name=name,
                    summary=analysis.summary, tags=tags,
                    sentiment=analysis.sentiment,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    source_type=source_type,
                    url=url,
                ))
                logs.append(AnalysisLogResponse(
                    analyzed_at=datetime.now(), symbol=symbol, name=name,
                    summary=analysis.summary, tags=tags,
                    sentiment=analysis.sentiment,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    source_type=source_type,
                    url=url,
                ))

            if report_best:
                analysis, source_type, url = report_best
                tags = [t.label for t in analysis.tags]
                report_summaries.append(StockSummaryResponse(
                    symbol=symbol, name=name,
                    summary=analysis.summary, tags=tags,
                    sentiment=analysis.sentiment,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    source_type=source_type,
                    url=url,
                ))
                logs.append(AnalysisLogResponse(
                    analyzed_at=datetime.now(), symbol=symbol, name=name,
                    summary=analysis.summary, tags=tags,
                    sentiment=analysis.sentiment,
                    sentiment_score=analysis.sentiment_score,
                    confidence=analysis.confidence,
                    source_type=source_type,
                    url=url,
                ))

            if news_best or report_best:
                results.append({"symbol": symbol, "skipped": False})
            else:
                results.append({"symbol": symbol, "skipped": True, "reason": "분석 실패"})

        self._progress(f"✅ 파이프라인 완료 — 뉴스 {len(summaries)}건, 공시·리포트 {len(report_summaries)}건")

        return {
            "message": "파이프라인 완료",
            "processed": results,
            "summaries": summaries,
            "report_summaries": report_summaries,
            "logs": logs,
        }

    async def _analyze_best(self, raw_articles, symbol):
        """주어진 raw_article 목록에서 가장 높은 confidence의 분석 결과 반환"""
        best_analysis = None
        best_source_type = None
        best_url = None

        for raw in raw_articles:
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
                    lang=raw.lang or "ko",
                ))

                analysis = await self._analysis_usecase.execute(normalized.id)

                if best_analysis is None or analysis.confidence > best_analysis.confidence:
                    best_analysis = analysis
                    best_source_type = raw.source_type
                    best_url = getattr(raw, "url", None)

            except Exception as e:
                logger.warning(f"[Pipeline] {symbol} 분석 실패: {e}")
                continue

        if best_analysis is None:
            return None
        return best_analysis, best_source_type, best_url
