"""투자 판단 워크플로우에서 수집된 뉴스 본문 (PostgreSQL JSONB)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB

from app.infrastructure.database.pg_session import PgBase


class InvestmentNewsContentORM(PgBase):
    __tablename__ = "investment_news_contents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # cross-DB key: MySQL investment_news.id 와 동기화
    article_id = Column(Integer, nullable=False, index=True)
    raw_data = Column(JSONB, nullable=False)  # {title, source, link, snippet, published_at, content}
    created_at = Column(DateTime, default=datetime.now)
