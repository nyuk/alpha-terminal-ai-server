from app.domains.stock_analyzer.application.response.sentiment_analysis_response import SentimentAnalysisResponse
from app.domains.stock_analyzer.application.usecase.sentiment_analysis_port import SentimentAnalysisPort
from app.domains.stock_normalizer.application.usecase.normalized_article_repository_port import NormalizedArticleRepositoryPort


class AnalyzeSentimentUseCase:
    def __init__(
        self,
        article_repository: NormalizedArticleRepositoryPort,
        sentiment_port: SentimentAnalysisPort,
    ):
        self._article_repository = article_repository
        self._sentiment_port = sentiment_port

    async def execute(self, article_id: str) -> SentimentAnalysisResponse:
        article = await self._article_repository.find_by_id(article_id)
        if article is None:
            raise ValueError(f"normalized_article not found: {article_id}")

        sentiment, score = await self._sentiment_port.analyze(
            title=article.title,
            body=article.body,
        )

        return SentimentAnalysisResponse(
            article_id=article_id,
            sentiment=sentiment,
            sentiment_score=score,
        )
