from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.pg_session import PgBase


class InvestmentYouTubeCommentORM(PgBase):
    """투자 워크플로우에서 수집된 YouTube 댓글 (PostgreSQL)."""

    __tablename__ = "investment_youtube_video_comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(20), nullable=False, index=True)
    comment_id = Column(String(100), nullable=False, unique=True, index=True)
    author_name = Column(String(200), nullable=False)
    text = Column(Text, nullable=False)
    published_at = Column(String(50), nullable=True)
    like_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
