from typing import List

from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import Session

from app.domains.stock.application.usecase.stock_repository_port import StockRepositoryPort
from app.domains.stock.domain.entity.stock import Stock
from app.domains.stock.infrastructure.mapper.stock_mapper import StockMapper
from app.domains.stock.infrastructure.orm.stock_orm import StockORM


class StockRepositoryImpl(StockRepositoryPort):

    def __init__(self, db: Session):
        self._db = db

    def search_by_name(self, keyword: str, limit: int = 20) -> List[Stock]:
        orms = (
            self._db.query(StockORM)
            .filter(StockORM.name.like(f"%{keyword}%"))
            .limit(limit)
            .all()
        )
        return [StockMapper.to_entity(o) for o in orms]

    def bulk_upsert(self, stocks: List[Stock]) -> int:
        if not stocks:
            return 0

        rows = [
            {"symbol": s.symbol, "name": s.name, "market": s.market, "corp_code": s.corp_code}
            for s in stocks
        ]

        stmt = insert(StockORM).values(rows)
        stmt = stmt.on_duplicate_key_update(
            name=stmt.inserted.name,
            market=stmt.inserted.market,
            corp_code=stmt.inserted.corp_code,
        )
        self._db.execute(stmt)
        self._db.commit()
        return len(rows)

    def count(self) -> int:
        return self._db.query(StockORM).count()
