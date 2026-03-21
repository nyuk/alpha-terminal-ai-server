from abc import ABC, abstractmethod
from typing import List

from app.domains.stock.domain.entity.stock import Stock


class DartCorpCodePort(ABC):

    @abstractmethod
    def fetch_all(self) -> List[Stock]:
        """DART에서 전체 상장사 기업코드 목록을 가져온다"""
        pass
