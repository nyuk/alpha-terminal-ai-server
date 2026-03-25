from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class WatchlistItem:
    symbol: str
    name: str
    market: Optional[str] = None
    account_id: Optional[int] = None
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
