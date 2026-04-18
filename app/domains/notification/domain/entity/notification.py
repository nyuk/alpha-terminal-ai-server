from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Notification:
    user_id: int
    title: str
    body: str
    is_read: bool = False
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
