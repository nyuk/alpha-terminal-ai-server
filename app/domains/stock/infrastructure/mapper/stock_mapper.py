from app.domains.stock.domain.entity.stock import Stock
from app.domains.stock.infrastructure.orm.stock_orm import StockORM


class StockMapper:

    @staticmethod
    def to_entity(orm: StockORM) -> Stock:
        return Stock(id=orm.id, symbol=orm.symbol, name=orm.name, market=orm.market, corp_code=orm.corp_code)

    @staticmethod
    def to_orm(entity: Stock) -> StockORM:
        return StockORM(symbol=entity.symbol, name=entity.name, market=entity.market, corp_code=entity.corp_code)
