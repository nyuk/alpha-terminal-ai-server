from typing import Optional, List

from sqlalchemy.orm import Session

from app.domains.watchlist.application.usecase.watchlist_repository_port import WatchlistRepositoryPort
from app.domains.watchlist.domain.entity.watchlist_item import WatchlistItem
from app.domains.watchlist.infrastructure.mapper.watchlist_item_mapper import WatchlistItemMapper
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM


class WatchlistRepositoryImpl(WatchlistRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def save(self, item: WatchlistItem) -> WatchlistItem:
        try:
            orm = WatchlistItemMapper.to_orm(item)
            self._db.add(orm)
            self._db.commit()
            self._db.refresh(orm)
            return WatchlistItemMapper.to_entity(orm)
        except Exception:
            self._db.rollback()
            raise

    def find_by_symbol(self, symbol: str, account_id: Optional[int] = None) -> Optional[WatchlistItem]:
        query = self._db.query(WatchlistItemORM).filter(WatchlistItemORM.symbol == symbol)
        if account_id is not None:
            query = query.filter(WatchlistItemORM.account_id == account_id)
        orm = query.first()
        if orm is None:
            return None
        return WatchlistItemMapper.to_entity(orm)

    def find_all(self, account_id: Optional[int] = None) -> List[WatchlistItem]:
        query = self._db.query(WatchlistItemORM)
        if account_id is not None:
            query = query.filter(WatchlistItemORM.account_id == account_id)
        orms = query.order_by(WatchlistItemORM.created_at.desc()).all()
        return [WatchlistItemMapper.to_entity(orm) for orm in orms]

    def delete_by_id(self, item_id: int) -> bool:
        try:
            orm = self._db.query(WatchlistItemORM).filter(WatchlistItemORM.id == item_id).first()
            if orm is None:
                return False
            self._db.delete(orm)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            raise
