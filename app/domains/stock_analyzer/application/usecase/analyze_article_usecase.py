from app.domains.stock_analyzer.application.request.analyze_article_request import AnalyzeArticleRequest
from app.domains.stock_analyzer.application.response.article_analysis_response import (
    ArticleAnalysisResponse,
    TagItemResponse,
)
from app.domains.stock_analyzer.application.usecase.article_analyzer_port import ArticleAnalyzerPort


class AnalyzeArticleUseCase:
    def __init__(self, analyzer_port: ArticleAnalyzerPort):
        self._analyzer = analyzer_port

    async def execute(self, request: AnalyzeArticleRequest) -> ArticleAnalysisResponse:
        analyzed = await self._analyzer.analyze(
            article_id=request.article_id,
            title=request.title,
            body=request.body,
            category=request.category,
        )

        return ArticleAnalysisResponse(
            article_id=analyzed.article_id,
            summary=analyzed.summary,
            tags=[TagItemResponse(label=t.label, category=t.category.value) for t in analyzed.tags],
            sentiment=analyzed.sentiment,
            sentiment_score=analyzed.sentiment_score,
            confidence=analyzed.confidence,
            analyzer_version=analyzed.analyzer_version,
        )
