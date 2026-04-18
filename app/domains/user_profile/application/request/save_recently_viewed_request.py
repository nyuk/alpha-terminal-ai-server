from typing import Optional

from pydantic import BaseModel


class SaveRecentlyViewedRequest(BaseModel):
    symbol: str
    name: str
    market: Optional[str] = None
