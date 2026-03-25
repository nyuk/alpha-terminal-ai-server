from typing import Optional

from pydantic import BaseModel


class MeResponse(BaseModel):
    is_registered: bool
    email: str
    nickname: Optional[str] = None
    account_id: Optional[str] = None
