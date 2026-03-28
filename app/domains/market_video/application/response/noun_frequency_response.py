from typing import List

from pydantic import BaseModel


class NounFrequencyItem(BaseModel):
    noun: str
    count: int


class WordCloudItem(BaseModel):
    """워드클라우드 시각화 라이브러리 호환 포맷 (text / value)."""
    text: str
    value: int


class NounFrequencyResponse(BaseModel):
    keywords: List[NounFrequencyItem]
    word_cloud_data: List[WordCloudItem]
    total_noun_count: int
    analyzed_video_count: int
