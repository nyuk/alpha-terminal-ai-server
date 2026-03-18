from abc import ABC, abstractmethod
from typing import Optional

from app.domains.stock_normalizer.domain.entity.normalized_article import NormalizedArticle


class NormalizedArticleRepositoryPort(ABC):
    @abstractmethod
    async def save(self, article: NormalizedArticle) -> NormalizedArticle:
        pass

    @abstractmethod
    async def find_by_id(self, article_id: str) -> Optional[NormalizedArticle]:
        pass
