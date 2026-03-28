from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.infrastructure.database.session import Base


class AccountORM(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    kakao_id = Column(String(50), nullable=False, unique=True)
    nickname = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    is_watchlist_public = Column(Boolean, default=False, nullable=False)
