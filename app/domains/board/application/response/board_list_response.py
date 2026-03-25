from datetime import datetime
from typing import List

from pydantic import BaseModel


class BoardListItemResponse(BaseModel):
    board_id: int
    title: str
    content: str
    nickname: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BoardListResponse(BaseModel):
    items: List[BoardListItemResponse]
    page: int
    total_pages: int
    total_count: int
