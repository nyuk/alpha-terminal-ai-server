from typing import List

from app.domains.stock.application.response.stock_response import StockResponse
from app.domains.stock.application.usecase.stock_repository_port import StockRepositoryPort


class SearchStockUseCase:

    def __init__(self, repository: StockRepositoryPort):
        self._repository = repository

    def execute(self, keyword: str) -> List[StockResponse]:
        stocks = self._repository.search_by_name(keyword)
        return [StockResponse(symbol=s.symbol, name=s.name, market=s.market) for s in stocks]
