from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.infrastructure.database.session import Base


class EventORM(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(30), nullable=False)  # visit | app_open | core_start | core_complete
    campaign = Column(String(50), nullable=True)     # team_referral | organic | ...
    occurred_at = Column(DateTime, default=datetime.now, nullable=False, index=True)
