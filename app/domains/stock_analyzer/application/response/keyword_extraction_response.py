from typing import List

from pydantic import BaseModel


class KeywordExtractionResponse(BaseModel):
    article_id: str
    keywords: List[str]
