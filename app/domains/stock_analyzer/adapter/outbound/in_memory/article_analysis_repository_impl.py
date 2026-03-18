from typing import Optional

from app.domains.stock_analyzer.application.usecase.article_analysis_repository_port import ArticleAnalysisRepositoryPort
from app.domains.stock_analyzer.domain.entity.analyzed_article import AnalyzedArticle


class InMemoryArticleAnalysisRepository(ArticleAnalysisRepositoryPort):
    def __init__(self):
        self._storage: dict[str, AnalyzedArticle] = {}

    async def save(self, analysis: AnalyzedArticle) -> AnalyzedArticle:
        self._storage[analysis.article_id] = analysis
        return analysis

    async def find_by_article_id(self, article_id: str) -> Optional[AnalyzedArticle]:
        return self._storage.get(article_id)
