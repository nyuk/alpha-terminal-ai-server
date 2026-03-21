from abc import ABC, abstractmethod
from typing import Optional

from app.domains.news_search.domain.entity.saved_article import SavedArticle


class SavedArticleRepositoryPort(ABC):
    @abstractmethod
    def save(self, article: SavedArticle) -> SavedArticle:
        pass

    @abstractmethod
    def find_by_link(self, link: str) -> Optional[SavedArticle]:
        pass

    @abstractmethod
    def find_by_id(self, article_id: int) -> Optional[SavedArticle]:
        pass
