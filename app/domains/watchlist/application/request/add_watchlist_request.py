from typing import Optional

from pydantic import BaseModel, Field


class AddWatchlistRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1)
    market: Optional[str] = None
