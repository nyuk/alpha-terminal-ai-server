from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.mysql import JSON

from app.infrastructure.database.session import Base


class AnalysisLogORM(Base):
    __tablename__ = "analysis_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analyzed_at = Column(DateTime, nullable=False, default=datetime.now)
    symbol = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)
    summary = Column(Text, nullable=False)
    tags = Column(JSON, nullable=True)
    sentiment = Column(String(20), nullable=False)
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    account_id = Column(Integer, nullable=True)
