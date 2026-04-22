from typing import Dict, List, Optional

from sqlalchemy import func, or_
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
        kw = keyword.strip()
        pattern = f"%{kw}%"
        pattern_sym = f"%{kw.lower()}%"
        orms = (
            self._db.query(StockORM)
            .filter(
                or_(
                    StockORM.name.like(pattern),
                    func.lower(StockORM.symbol).like(pattern_sym),
                )
            )
            .limit(limit)
            .all()
        )
        return [StockMapper.to_entity(o) for o in orms]

    def find_market_by_symbol(self, symbol: str) -> Optional[str]:
        row = self._db.query(StockORM).filter(StockORM.symbol == symbol).one_or_none()
        return row.market if row else None

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
        try:
            self._db.execute(stmt)
            self._db.commit()
            return len(rows)
        except Exception:
            self._db.rollback()
            raise

    def count(self) -> int:
        return self._db.query(StockORM).count()

    def find_by_symbol(self, symbol: str) -> Optional[Stock]:
        orm = self._db.query(StockORM).filter(StockORM.symbol == symbol).first()
        if orm is None:
            return None
        return StockMapper.to_entity(orm)

    def update_market_bulk(self, market_map: Dict[str, str]) -> int:
        if not market_map:
            return 0
        try:
            updated = 0
            for symbol, market in market_map.items():
                count = (
                    self._db.query(StockORM)
                    .filter(StockORM.symbol == symbol)
                    .update({"market": market})
                )
                updated += count
            self._db.commit()
            return updated
        except Exception:
            self._db.rollback()
            raise
