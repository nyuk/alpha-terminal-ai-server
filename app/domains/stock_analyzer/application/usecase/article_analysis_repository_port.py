from abc import ABC, abstractmethod
from typing import Optional

from app.domains.stock_analyzer.domain.entity.analyzed_article import AnalyzedArticle


class ArticleAnalysisRepositoryPort(ABC):
    @abstractmethod
    async def save(self, analysis: AnalyzedArticle) -> AnalyzedArticle:
        pass

    @abstractmethod
    async def find_by_article_id(self, article_id: str) -> Optional[AnalyzedArticle]:
        pass
