from abc import ABC, abstractmethod

from app.domains.stock_analyzer.domain.entity.analyzed_article import AnalyzedArticle


class ArticleAnalyzerPort(ABC):
    @abstractmethod
    async def analyze(self, article_id: str, title: str, body: str, category: str) -> AnalyzedArticle:
        pass
