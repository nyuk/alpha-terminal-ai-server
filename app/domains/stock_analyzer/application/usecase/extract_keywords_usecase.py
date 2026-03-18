from app.domains.stock_analyzer.application.response.keyword_extraction_response import KeywordExtractionResponse
from app.domains.stock_analyzer.application.usecase.keyword_extraction_port import KeywordExtractionPort
from app.domains.stock_normalizer.application.usecase.normalized_article_repository_port import NormalizedArticleRepositoryPort


class ExtractKeywordsUseCase:
    def __init__(
        self,
        article_repository: NormalizedArticleRepositoryPort,
        keyword_port: KeywordExtractionPort,
    ):
        self._article_repository = article_repository
        self._keyword_port = keyword_port

    async def execute(self, article_id: str) -> KeywordExtractionResponse:
        article = await self._article_repository.find_by_id(article_id)
        if article is None:
            raise ValueError(f"normalized_article not found: {article_id}")

        keywords = await self._keyword_port.extract(
            title=article.title,
            body=article.body,
        )

        return KeywordExtractionResponse(article_id=article_id, keywords=keywords)
