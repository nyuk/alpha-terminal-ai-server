from app.domains.watchlist.domain.entity.watchlist_item import WatchlistItem
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM


class WatchlistItemMapper:
    @staticmethod
    def to_entity(orm: WatchlistItemORM) -> WatchlistItem:
        return WatchlistItem(
            id=orm.id,
            account_id=orm.account_id,
            symbol=orm.symbol,
            name=orm.name,
            market=orm.market,
            created_at=orm.created_at,
        )

    @staticmethod
    def to_orm(entity: WatchlistItem) -> WatchlistItemORM:
        return WatchlistItemORM(
            account_id=entity.account_id,
            symbol=entity.symbol,
            name=entity.name,
            market=entity.market,
        )
