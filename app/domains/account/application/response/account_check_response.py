from typing import Optional

from pydantic import BaseModel


class AccountCheckResponse(BaseModel):
    is_registered: bool
    account_id: Optional[int] = None
    email: str
    nickname: Optional[str] = None
