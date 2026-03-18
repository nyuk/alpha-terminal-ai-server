from app.domains.stock_analyzer.application.response.risk_tagging_response import RiskTaggingResponse, RiskTagResponse
from app.domains.stock_analyzer.application.usecase.risk_tagging_port import RiskTaggingPort
from app.domains.stock_normalizer.application.usecase.normalized_article_repository_port import NormalizedArticleRepositoryPort


class GenerateRiskTagsUseCase:
    def __init__(
        self,
        article_repository: NormalizedArticleRepositoryPort,
        risk_tagging_port: RiskTaggingPort,
    ):
        self._article_repository = article_repository
        self._risk_tagging_port = risk_tagging_port

    async def execute(self, article_id: str) -> RiskTaggingResponse:
        article = await self._article_repository.find_by_id(article_id)
        if article is None:
            raise ValueError(f"normalized_article not found: {article_id}")

        tags = await self._risk_tagging_port.tag(
            title=article.title,
            body=article.body,
        )

        return RiskTaggingResponse(
            article_id=article_id,
            risk_tags=[RiskTagResponse(label=t.label, category=t.category.value) for t in tags],
        )
