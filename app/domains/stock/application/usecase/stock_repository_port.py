from abc import ABC, abstractmethod
from typing import List, Optional

from app.domains.stock.domain.entity.stock import Stock


class StockRepositoryPort(ABC):

    @abstractmethod
    def search_by_name(self, keyword: str, limit: int = 20) -> List[Stock]:
        pass

    @abstractmethod
    def bulk_upsert(self, stocks: List[Stock]) -> int:
        """저장/업데이트 후 처리된 건수 반환"""
        pass

    @abstractmethod
    def count(self) -> int:
        pass

    @abstractmethod
    def find_by_symbol(self, symbol: str) -> Optional[Stock]:
        pass
