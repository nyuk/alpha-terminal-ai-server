import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.domains.stock_collector.adapter.outbound.external.dart_collector_adapter import DartCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.google_news_rss_collector_adapter import GoogleNewsRssCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.naver_blog_cafe_collector_adapter import NaverBlogCafeCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.news_collector_adapter import NewsCollectorAdapter
from app.domains.stock_collector.adapter.outbound.external.twitter_collector_adapter import TwitterCollectorAdapter
from app.domains.stock_collector.adapter.outbound.persistence.raw_article_repository_impl import RawArticleRepositoryImpl
from app.domains.stock_collector.application.request.collect_request import CollectRequest
from app.domains.stock_collector.application.response.article_response import ArticleResponse
from app.domains.stock_collector.application.response.collect_response import CollectResponse
from app.domains.stock_collector.application.usecase.collect_articles_usecase import CollectArticlesUseCase
from app.domains.stock_collector.application.usecase.get_articles_usecase import GetArticlesUseCase
from app.domains.stock.adapter.outbound.persistence.stock_repository_impl import StockRepositoryImpl
from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stock-collector", tags=["stock-collector"])

# 한글 종목명 → 종목 코드 마이그레이션 매핑
_NAME_TO_CODE = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "네이버": "035420",
    "카카오": "035720",
    "LG에너지솔루션": "373220",
    "현대자동차": "005380",
    "기아": "000270",
    "LG화학": "051910",
    "삼성SDI": "006400",
    "셀트리온": "068270",
}


@router.post("/collect", response_model=CollectResponse, status_code=200)
async def collect_articles(request: CollectRequest, db: Session = Depends(get_db)):
    repository = RawArticleRepositoryImpl(db)
    stock_repository = StockRepositoryImpl(db)
    collectors = [DartCollectorAdapter(), NewsCollectorAdapter(), GoogleNewsRssCollectorAdapter(), NaverBlogCafeCollectorAdapter()]
    usecase = CollectArticlesUseCase(repository, collectors, stock_repository=stock_repository)
    return usecase.execute(request.symbol)


@router.post("/admin/migrate-symbols")
async def migrate_symbols(db: Session = Depends(get_db)):
    """DB에 한글 종목명으로 저장된 symbol을 종목 코드로 일괄 업데이트한다."""
    repository = RawArticleRepositoryImpl(db)
    results = {}
    total = 0
    for korean_name, code in _NAME_TO_CODE.items():
        count = repository.migrate_symbol(old_symbol=korean_name, new_symbol=code)
        if count > 0:
            results[korean_name] = {"code": code, "updated": count}
            total += count
            logger.debug(f"[MigrateSymbols] '{korean_name}' → '{code}': {count}건 업데이트")
    return {"total_updated": total, "details": results}


@router.get("/articles", response_model=List[ArticleResponse])
async def get_articles(
    symbol: Optional[str] = Query(default=None),
    source_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    repository = RawArticleRepositoryImpl(db)
    usecase = GetArticlesUseCase(repository)
    return usecase.execute(symbol=symbol, source_type=source_type)
