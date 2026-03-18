from abc import ABC, abstractmethod
from typing import Tuple


class SentimentAnalysisPort(ABC):
    @abstractmethod
    async def analyze(self, title: str, body: str) -> Tuple[str, float]:
        """Returns (sentiment, sentiment_score)"""
        pass
