from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class NotificationORM(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.now)
