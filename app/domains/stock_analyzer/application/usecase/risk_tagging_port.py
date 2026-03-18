from abc import ABC, abstractmethod
from typing import List

from app.domains.stock_analyzer.domain.entity.tag_item import TagItem


class RiskTaggingPort(ABC):
    @abstractmethod
    async def tag(self, title: str, body: str) -> List[TagItem]:
        pass
