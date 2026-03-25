from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalysisLogResponse(BaseModel):
    analyzed_at: datetime
    symbol: str
    name: str
    summary: str
    tags: list[str]
    sentiment: str
    sentiment_score: float
    confidence: float
    account_id: Optional[int] = None
