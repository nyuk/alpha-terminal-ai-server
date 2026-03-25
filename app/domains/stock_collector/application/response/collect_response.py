from typing import List, Optional

from pydantic import BaseModel


class CollectedItem(BaseModel):
    id: Optional[int] = None
    source_type: str
    source_name: str = ""
    title: str


class CollectResponse(BaseModel):
    symbol: str
    total_collected: int
    total_skipped: int
    items: List[CollectedItem]
