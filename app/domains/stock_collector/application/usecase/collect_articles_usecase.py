import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.domains.stock_collector.application.usecase.collector_port import CollectorPort
from app.domains.stock_collector.application.usecase.raw_article_repository_port import RawArticleRepositoryPort
from app.domains.stock_collector.application.response.collect_response import CollectResponse, CollectedItem
from app.domains.stock_collector.domain.entity.raw_article import RawArticle
from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

NEWS_SOURCE_TYPES = {"NEWS"}
REPORT_SOURCE_TYPES = {"DISCLOSURE", "REPORT"}


def _get_collected_dt(raw: RawArticle) -> datetime:
    created_at = getattr(raw, "created_at", None)
    if isinstance(created_at, datetime):
        return created_at.replace(tzinfo=None) if created_at.tzinfo else created_at

    s = str(getattr(raw, "collected_at", "") or "").strip()
    if not s:
        return datetime.min
    try:
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except ValueError:
        return datetime.min


def _has_fresh_article(articles: List[RawArticle], source_types: set[str], cutoff: datetime) -> bool:
    return any(
        article.source_type in source_types and _get_collected_dt(article) >= cutoff
        for article in articles
    )


def _can_reuse_recent_collection(articles: List[RawArticle], symbol: str, fresh_minutes: int) -> bool:
    if fresh_minutes <= 0 or not articles:
        return False

    cutoff = datetime.now() - timedelta(minutes=fresh_minutes)
    if not _has_fresh_article(articles, NEWS_SOURCE_TYPES, cutoff):
        return False

    is_korean_stock = symbol.isdigit() and len(symbol) == 6
    if is_korean_stock:
        return _has_fresh_article(articles, REPORT_SOURCE_TYPES, cutoff)

    return True


class CollectArticlesUseCase:
    def __init__(
        self,
        repository: RawArticleRepositoryPort,
        collectors: List[CollectorPort],
        stock_repository=None,
    ):
        self._repository = repository
        self._collectors = collectors
        self._stock_repository = stock_repository

    def execute(self, symbol: str) -> CollectResponse:
        # DB에서 종목 정보 조회
        stock_name = symbol
        corp_code = ""

        if self._stock_repository:
            stock = self._stock_repository.find_by_symbol(symbol)
            if stock:
                stock_name = stock.name
                corp_code = stock.corp_code
            else:
                logger.warning(f"[Collector] stocks 테이블에 미등록 심볼: {symbol} — 수집을 건너뜁니다.")
                return CollectResponse(symbol=symbol, total_collected=0, total_skipped=0, items=[])

        existing_articles = self._repository.find_all(symbol=symbol)
        fresh_minutes = get_settings().pipeline_collection_fresh_minutes
        if _can_reuse_recent_collection(existing_articles, symbol, fresh_minutes):
            logger.info(
                "[Collector] recent raw articles reused: symbol=%s count=%d fresh_minutes=%d",
                symbol,
                len(existing_articles),
                fresh_minutes,
            )
            return CollectResponse(
                symbol=symbol,
                total_collected=0,
                total_skipped=len(existing_articles),
                items=[],
            )

        collected_items = []
        total_collected = 0
        total_skipped = 0

        for collector in self._collectors:
            articles = collector.collect(symbol, stock_name, corp_code)

            for article in articles:
                existing = self._repository.find_by_dedup_key(
                    article.source_type, article.source_doc_id
                )
                if existing:
                    total_skipped += 1
                    continue

                saved = self._repository.save(article)
                collected_items.append(
                    CollectedItem(
                        id=saved.id,
                        source_type=saved.source_type,
                        source_name=saved.source_name,
                        title=saved.title,
                    )
                )
                total_collected += 1

        return CollectResponse(
            symbol=symbol,
            total_collected=total_collected,
            total_skipped=total_skipped,
            items=collected_items,
        )
