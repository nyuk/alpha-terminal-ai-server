from typing import Optional

from pydantic import BaseModel


class SaveInterestArticleResponse(BaseModel):
    id: int
    title: str
    source: Optional[str] = None
    link: str
    published_at: Optional[str] = None
    content: str
