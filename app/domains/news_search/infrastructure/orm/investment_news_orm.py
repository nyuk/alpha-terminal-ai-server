"""투자 판단 워크플로우에서 수집된 뉴스 메타데이터 (MySQL)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class InvestmentNewsORM(Base):
    __tablename__ = "investment_news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company = Column(String(200), nullable=True)
    keyword = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    source = Column(String(200), nullable=False, default="")
    link = Column(Text, nullable=False)
    link_hash = Column(String(64), nullable=False, unique=True, index=True)
    snippet = Column(Text, nullable=True)
    published_at = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
