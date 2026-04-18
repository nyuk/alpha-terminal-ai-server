from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.infrastructure.database.session import Base


class UserInteractionORM(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    interaction_type = Column(String(20), nullable=False)   # like / comment / click
    count = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=True)
    name = Column(String(100), nullable=True)
    market = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
