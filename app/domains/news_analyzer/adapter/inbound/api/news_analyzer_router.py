from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.news_analyzer.adapter.outbound.external.openai_analysis_adapter import OpenAIAnalysisAdapter
from app.domains.news_analyzer.adapter.outbound.persistence.saved_article_query_impl import SavedArticleQueryImpl
from app.domains.news_analyzer.application.request.analyze_article_request import AnalyzeArticleRequest
from app.domains.news_analyzer.application.response.analyze_article_response import AnalyzeArticleResponse
from app.domains.news_analyzer.application.usecase.analyze_article_usecase import AnalyzeArticleUseCase
from app.domains.news_analyzer.application.usecase.exceptions import ArticleNotFoundError, EmptyContentError
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/news-analyzer", tags=["news-analyzer"])


@router.post("/analyze", response_model=AnalyzeArticleResponse)
async def analyze_article(request: AnalyzeArticleRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    article_query = SavedArticleQueryImpl(db)
    analyzer = OpenAIAnalysisAdapter(api_key=settings.openai_api_key)
    usecase = AnalyzeArticleUseCase(article_query, analyzer)
    try:
        return usecase.execute(request)
    except ArticleNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except EmptyContentError as e:
        raise HTTPException(status_code=422, detail=str(e))
