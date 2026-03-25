from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Board:
    title: str
    content: str
    account_id: int
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
