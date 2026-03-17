from typing import List

from pydantic import BaseModel


class TagItemResponse(BaseModel):
    label: str
    category: str  # CAPITAL | EARNINGS | PRODUCT | MANAGEMENT | INDUSTRY | RISK | OTHER


class ArticleAnalysisResponse(BaseModel):
    article_id: str
    summary: str
    tags: List[TagItemResponse]
    sentiment: str          # POSITIVE | NEGATIVE | NEUTRAL
    sentiment_score: float  # -1.0 ~ 1.0
    confidence: float       # 0.0 ~ 1.0
    analyzer_version: str
