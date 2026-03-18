from typing import Optional

from app.domains.stock_normalizer.application.usecase.normalized_article_repository_port import NormalizedArticleRepositoryPort
from app.domains.stock_normalizer.domain.entity.normalized_article import NormalizedArticle


class InMemoryNormalizedArticleRepository(NormalizedArticleRepositoryPort):
    def __init__(self):
        self._storage: dict[str, NormalizedArticle] = {}

    async def save(self, article: NormalizedArticle) -> NormalizedArticle:
        self._storage[article.id] = article
        return article

    async def find_by_id(self, article_id: str) -> Optional[NormalizedArticle]:
        return self._storage.get(article_id)
