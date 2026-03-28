from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from app.domains.market_video.domain.entity.market_video import MarketVideo


class MarketVideoRepositoryPort(ABC):
    @abstractmethod
    def upsert_all(self, videos: List[MarketVideo]) -> List[MarketVideo]:
        """videoId 기준 upsert. 성공한 영상만 반환한다."""
        pass

    @abstractmethod
    def find_paginated(
        self,
        page: int,
        page_size: int,
        stock_name: Optional[str] = None,
    ) -> Tuple[List[MarketVideo], int]:
        """
        :return: (videos, total_count)
        stock_name이 있으면 title에 포함된 영상만 반환한다.
        """
        pass
