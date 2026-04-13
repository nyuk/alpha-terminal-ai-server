"""BL-BE-60: 기사 본문 및 비정형 원본 데이터 PostgreSQL JSONB 저장 ORM."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB

from app.infrastructure.database.pg_session import PgBase


class SavedArticleContentORM(PgBase):
    __tablename__ = "interest_article_contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, nullable=False, index=True)
    account_id = Column(Integer, nullable=False, index=True)
    raw_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
