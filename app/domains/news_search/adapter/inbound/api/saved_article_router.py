from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.news_search.adapter.outbound.external.article_content_adapter import ArticleContentAdapter
from app.domains.news_search.adapter.outbound.external.openai_analysis_adapter import OpenAIAnalysisAdapter
from app.domains.news_search.adapter.outbound.external.serp_news_search_adapter import SerpNewsSearchAdapter
from app.domains.news_search.adapter.outbound.persistence.saved_article_repository_impl import SavedArticleRepositoryImpl
from app.domains.news_search.application.request.analyze_article_request import AnalyzeArticleRequest
from app.domains.news_search.application.request.bulk_analyze_request import BulkAnalyzeRequest
from app.domains.news_search.application.request.save_article_request import SaveArticleRequest
from app.domains.news_search.application.response.analyze_article_response import AnalyzeArticleResponse
from app.domains.news_search.application.response.bulk_analyze_response import BulkAnalyzeResponse
from app.domains.news_search.application.response.save_article_response import SaveArticleResponse
from app.domains.news_search.application.usecase.analyze_article_usecase import AnalyzeArticleUseCase
from app.domains.news_search.application.usecase.bulk_analyze_usecase import BulkAnalyzeUseCase
from app.domains.news_search.application.usecase.save_article_usecase import SaveArticleUseCase
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/news", tags=["news"])

_settings = get_settings()
_analysis_adapter = OpenAIAnalysisAdapter(api_key=_settings.openai_api_key)


@router.post("/saved", response_model=SaveArticleResponse, status_code=201)
async def save_article(request: SaveArticleRequest, db: Session = Depends(get_db)):
    repository = SavedArticleRepositoryImpl(db)
    content_fetcher = ArticleContentAdapter()
    usecase = SaveArticleUseCase(repository, content_fetcher)
    try:
        return usecase.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/saved/{article_id}/analysis", response_model=AnalyzeArticleResponse)
async def analyze_article(article_id: int, db: Session = Depends(get_db)):
    repository = SavedArticleRepositoryImpl(db)
    usecase = AnalyzeArticleUseCase(repository, _analysis_adapter)
    try:
        return await usecase.execute(AnalyzeArticleRequest(article_id=article_id))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/bulk-analysis", response_model=BulkAnalyzeResponse)
async def bulk_analyze(request: BulkAnalyzeRequest, db: Session = Depends(get_db)):
    usecase = BulkAnalyzeUseCase(
        news_search_port=SerpNewsSearchAdapter(),
        repository=SavedArticleRepositoryImpl(db),
        content_fetcher=ArticleContentAdapter(),
        analysis_port=_analysis_adapter,
    )
    return await usecase.execute(request)
