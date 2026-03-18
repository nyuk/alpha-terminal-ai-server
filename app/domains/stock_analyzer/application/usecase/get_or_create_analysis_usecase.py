from app.domains.stock_analyzer.application.response.article_analysis_response import ArticleAnalysisResponse, TagItemResponse
from app.domains.stock_analyzer.application.usecase.article_analysis_repository_port import ArticleAnalysisRepositoryPort
from app.domains.stock_analyzer.application.usecase.article_analyzer_port import ArticleAnalyzerPort
from app.domains.stock_normalizer.application.usecase.normalized_article_repository_port import NormalizedArticleRepositoryPort


class GetOrCreateAnalysisUseCase:
    def __init__(
        self,
        article_repository: NormalizedArticleRepositoryPort,
        analysis_repository: ArticleAnalysisRepositoryPort,
        analyzer_port: ArticleAnalyzerPort,
    ):
        self._article_repository = article_repository
        self._analysis_repository = analysis_repository
        self._analyzer_port = analyzer_port

    async def execute(self, article_id: str) -> ArticleAnalysisResponse:
        # 중복 분석 방지 — 기존 결과 있으면 반환
        existing = await self._analysis_repository.find_by_article_id(article_id)
        if existing:
            return ArticleAnalysisResponse(
                article_id=existing.article_id,
                summary=existing.summary,
                tags=[TagItemResponse(label=t.label, category=t.category.value) for t in existing.tags],
                sentiment=existing.sentiment,
                sentiment_score=existing.sentiment_score,
                confidence=existing.confidence,
                analyzer_version=existing.analyzer_version,
            )

        article = await self._article_repository.find_by_id(article_id)
        if article is None:
            raise ValueError(f"normalized_article not found: {article_id}")

        analyzed = await self._analyzer_port.analyze(
            article_id=article_id,
            title=article.title,
            body=article.body,
            category=article.category.value,
        )

        saved = await self._analysis_repository.save(analyzed)

        return ArticleAnalysisResponse(
            article_id=saved.article_id,
            summary=saved.summary,
            tags=[TagItemResponse(label=t.label, category=t.category.value) for t in saved.tags],
            sentiment=saved.sentiment,
            sentiment_score=saved.sentiment_score,
            confidence=saved.confidence,
            analyzer_version=saved.analyzer_version,
        )
