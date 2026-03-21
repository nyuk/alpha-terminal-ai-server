from typing import Optional

from pydantic import BaseModel


class MeResponse(BaseModel):
    isTemporary: bool
    email: str
    nickname: Optional[str] = None
