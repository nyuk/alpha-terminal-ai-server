from fastapi import APIRouter, Depends

from app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter import OpenAIAnalyzerAdapter
from app.domains.stock_analyzer.application.request.analyze_article_request import AnalyzeArticleRequest
from app.domains.stock_analyzer.application.response.article_analysis_response import ArticleAnalysisResponse
from app.domains.stock_analyzer.application.usecase.analyze_article_usecase import AnalyzeArticleUseCase
from app.infrastructure.config.settings import get_settings

router = APIRouter(prefix="/analyzer", tags=["analyzer"])


def get_analyze_article_usecase() -> AnalyzeArticleUseCase:
    settings = get_settings()
    adapter = OpenAIAnalyzerAdapter(api_key=settings.openai_api_key)
    return AnalyzeArticleUseCase(analyzer_port=adapter)


@router.post("/articles", response_model=ArticleAnalysisResponse)
async def analyze_article(
    request: AnalyzeArticleRequest,
    usecase: AnalyzeArticleUseCase = Depends(get_analyze_article_usecase),
) -> ArticleAnalysisResponse:
    return await usecase.execute(request)
