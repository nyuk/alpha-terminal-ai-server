from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Account:
    email: str
    kakao_id: str
    nickname: str
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
