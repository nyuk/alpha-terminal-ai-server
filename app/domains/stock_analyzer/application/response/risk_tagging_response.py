from typing import List

from pydantic import BaseModel


class RiskTagResponse(BaseModel):
    label: str
    category: str  # 주로 RISK


class RiskTaggingResponse(BaseModel):
    article_id: str
    risk_tags: List[RiskTagResponse]
