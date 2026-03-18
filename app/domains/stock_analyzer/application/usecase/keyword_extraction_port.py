from abc import ABC, abstractmethod
from typing import List


class KeywordExtractionPort(ABC):
    @abstractmethod
    async def extract(self, title: str, body: str) -> List[str]:
        pass
