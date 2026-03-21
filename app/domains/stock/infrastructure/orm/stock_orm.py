from sqlalchemy import Column, Index, Integer, String

from app.infrastructure.database.session import Base


class StockORM(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    market = Column(String(10), nullable=False)
    corp_code = Column(String(20), nullable=False)

    __table_args__ = (
        Index("ix_stocks_name", "name"),
    )
