from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class InvestmentYouTubeLogORM(Base):
    """투자 워크플로우 YouTube 수집 실행 로그 (MySQL)."""

    __tablename__ = "investment_youtube_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    query = Column(Text, nullable=False)
    company = Column(String(200), nullable=True)
    video_count = Column(Integer, default=0)
    status = Column(String(20), nullable=False, default="success")  # success | partial | failed
    created_at = Column(DateTime, default=datetime.now)
