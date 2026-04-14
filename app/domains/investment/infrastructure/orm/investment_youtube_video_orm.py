from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class InvestmentYouTubeVideoORM(Base):
    """투자 워크플로우에서 수집된 YouTube 영상 (MySQL)."""

    __tablename__ = "investment_youtube_videos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(Integer, nullable=False, index=True)
    video_id = Column(String(20), nullable=False, index=True)
    title = Column(Text, nullable=False)
    channel_name = Column(String(200), nullable=False)
    published_at = Column(DateTime, nullable=True)
    video_url = Column(Text, nullable=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
