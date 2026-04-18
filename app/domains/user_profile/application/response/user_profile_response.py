from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class LikeHistoryItem(BaseModel):
    symbol: str
    count: int


class InteractionHistoryResponse(BaseModel):
    likes: List[LikeHistoryItem] = []
    comments: List[str] = []


class WatchlistSummaryItem(BaseModel):
    symbol: str
    name: str
    market: Optional[str] = None


class RecentlyViewedItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    market: Optional[str] = None
    viewed_at: datetime


class SaveRecentlyViewedResponse(BaseModel):
    symbol: str
    name: str
    market: Optional[str] = None
    viewed_at: datetime


class ClickedCardItem(BaseModel):
    symbol: str
    count: int


class UserProfileResponse(BaseModel):
    account_id: int
    watchlist: List[WatchlistSummaryItem] = []
    recently_viewed: List[RecentlyViewedItem] = []
    clicked_cards: List[ClickedCardItem] = []
    preferred_stocks: List[str] = []
    interaction_history: InteractionHistoryResponse = InteractionHistoryResponse()
    interests_text: str = ""
