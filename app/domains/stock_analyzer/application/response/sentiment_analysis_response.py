from pydantic import BaseModel


class SentimentAnalysisResponse(BaseModel):
    article_id: str
    sentiment: str        # POSITIVE | NEGATIVE | NEUTRAL
    sentiment_score: float  # -1.0 ~ 1.0
