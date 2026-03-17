from dataclasses import dataclass
from typing import List

from app.domains.stock_analyzer.domain.entity.tag_item import TagItem


@dataclass
class AnalyzedArticle:
    article_id: str
    summary: str
    tags: List[TagItem]
    sentiment: str        # POSITIVE | NEGATIVE | NEUTRAL
    sentiment_score: float  # -1.0 ~ 1.0
    confidence: float     # 0.0 ~ 1.0
    analyzer_version: str
