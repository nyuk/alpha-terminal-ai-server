from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.news_search.adapter.outbound.external.openai_analysis_adapter import OpenAIAnalysisAdapter
from app.domains.news_search.adapter.outbound.external.serp_news_search_adapter import SerpNewsSearchAdapter
from app.domains.news_search.adapter.outbound.persistence.article_content_store_impl import ArticleContentStoreImpl
from app.domains.news_search.adapter.outbound.persistence.saved_article_repository_impl import SavedArticleRepositoryImpl
from app.domains.news_search.application.request.analyze_article_request import AnalyzeArticleRequest
from app.domains.news_search.application.request.bulk_analyze_request import BulkAnalyzeRequest
from app.domains.news_search.application.request.save_article_request import SaveArticleRequest
from app.domains.news_search.application.response.analyze_article_response import AnalyzeArticleResponse
from app.domains.news_search.application.response.bulk_analyze_response import BulkAnalyzeResponse
from app.domains.news_search.application.response.save_article_response import SaveArticleResponse
from app.domains.news_search.application.response.save_interest_article_response import SaveInterestArticleResponse
from app.domains.news_search.application.response.saved_article_item_response import SavedArticleListResponse
from app.domains.news_search.application.usecase.analyze_article_usecase import AnalyzeArticleUseCase
from app.domains.news_search.application.usecase.bulk_analyze_usecase import BulkAnalyzeUseCase
from app.domains.news_search.application.usecase.list_saved_articles_usecase import ListSavedArticlesUseCase
from app.domains.news_search.application.usecase.save_article_usecase import SaveArticleUseCase
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.pg_session import get_pg_db
from app.infrastructure.database.session import get_db
from app.infrastructure.external.article_content_fetcher import ArticleContentFetcher

_content_fetcher = ArticleContentFetcher()

router = APIRouter(prefix="/news", tags=["news"])

_settings = get_settings()
_analysis_adapter = OpenAIAnalysisAdapter(api_key=_settings.openai_api_key)


@router.get("/saved", response_model=SavedArticleListResponse)
async def list_saved_articles(
    db: Session = Depends(get_db),
    pg_db: Session = Depends(get_pg_db),
    account_id: Optional[str] = Cookie(default=None),
):
    if account_id is None:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    repository = SavedArticleRepositoryImpl(db)
    content_store = ArticleContentStoreImpl(pg_db)
    usecase = ListSavedArticlesUseCase(repository, content_store)
    return usecase.execute(int(account_id))


@router.post("/interest-articles", response_model=SaveInterestArticleResponse, status_code=201)
async def save_interest_article(
    request: SaveArticleRequest,
    db: Session = Depends(get_db),
    pg_db: Session = Depends(get_pg_db),
    account_id: Optional[str] = Cookie(default=None),
):
    if account_id is None:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    parsed_account_id = int(account_id)

    repository = SavedArticleRepositoryImpl(db)
    content_store = ArticleContentStoreImpl(pg_db)
    usecase = SaveArticleUseCase(repository, content_store, _content_fetcher)
    try:
        result = usecase.execute(request, account_id=parsed_account_id)
        content = content_store.get_content(result.id) or ""
        return SaveInterestArticleResponse(
            id=result.id,
            title=request.title,
            source=request.source or "",
            link=request.link,
            published_at=request.published_at,
            content=content,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/saved", response_model=SaveArticleResponse, status_code=201)
async def save_article(
    request: SaveArticleRequest,
    db: Session = Depends(get_db),
    pg_db: Session = Depends(get_pg_db),
    account_id: Optional[str] = Cookie(default=None),
):
    if account_id is None:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    parsed_account_id = int(account_id)

    repository = SavedArticleRepositoryImpl(db)
    content_store = ArticleContentStoreImpl(pg_db)
    usecase = SaveArticleUseCase(repository, content_store, _content_fetcher)
    try:
        return usecase.execute(request, account_id=parsed_account_id)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/saved/{article_id}/analysis", response_model=AnalyzeArticleResponse)
async def analyze_article(
    article_id: int,
    db: Session = Depends(get_db),
    pg_db: Session = Depends(get_pg_db),
):
    repository = SavedArticleRepositoryImpl(db)
    content_store = ArticleContentStoreImpl(pg_db)
    usecase = AnalyzeArticleUseCase(repository, _analysis_adapter, content_store)
    try:
        return await usecase.execute(AnalyzeArticleRequest(article_id=article_id))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/bulk-analysis", response_model=BulkAnalyzeResponse)
async def bulk_analyze(
    request: BulkAnalyzeRequest,
    db: Session = Depends(get_db),
    pg_db: Session = Depends(get_pg_db),
    account_id: Optional[str] = Cookie(default=None),
):
    parsed_account_id = int(account_id) if account_id else None
    usecase = BulkAnalyzeUseCase(
        news_search_port=SerpNewsSearchAdapter(),
        repository=SavedArticleRepositoryImpl(db),
        content_store=ArticleContentStoreImpl(pg_db),
        analysis_port=_analysis_adapter,
    )
    return await usecase.execute(request, account_id=parsed_account_id)
