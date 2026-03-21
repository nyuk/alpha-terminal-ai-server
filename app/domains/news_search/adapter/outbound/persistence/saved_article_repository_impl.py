from hashlib import sha256
from typing import Optional

from sqlalchemy.orm import Session

from app.domains.news_search.application.usecase.saved_article_repository_port import SavedArticleRepositoryPort
from app.domains.news_search.domain.entity.saved_article import SavedArticle
from app.domains.news_search.infrastructure.mapper.saved_article_mapper import SavedArticleMapper
from app.domains.news_search.infrastructure.orm.saved_article_orm import SavedArticleORM


class SavedArticleRepositoryImpl(SavedArticleRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def save(self, article: SavedArticle) -> SavedArticle:
        orm = SavedArticleMapper.to_orm(article)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return SavedArticleMapper.to_entity(orm)

    def find_by_link(self, link: str) -> Optional[SavedArticle]:
        link_hash = sha256(link.encode()).hexdigest()
        orm = self._db.query(SavedArticleORM).filter(SavedArticleORM.link_hash == link_hash).first()
        if orm is None:
            return None
        return SavedArticleMapper.to_entity(orm)

    def find_by_id(self, article_id: int) -> Optional[SavedArticle]:
        orm = self._db.query(SavedArticleORM).filter(SavedArticleORM.id == article_id).first()
        if orm is None:
            return None
        return SavedArticleMapper.to_entity(orm)
