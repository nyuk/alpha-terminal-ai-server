from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.investment.adapter.outbound.external.youtube_sentiment_adapter import YouTubeSentimentAdapter
from app.domains.investment.application.request.youtube_sentiment_request import YouTubeSentimentRequest
from app.domains.investment.application.response.youtube_sentiment_response import (
    SentimentDistribution,
    YouTubeSentimentResponse,
)
from app.domains.investment.application.usecase.youtube_sentiment_usecase import YouTubeSentimentUseCase
from app.infrastructure.cache.redis_client import redis_client

router = APIRouter(prefix="/investment", tags=["legacy-investment"])

_session_adapter = RedisSessionAdapter(redis_client)

_DISABLED_DECISION_DETAIL = (
    "The investment decision API is disabled in StockBrief. "
    "Use fact-based watchlist summaries, source links, and risk briefings instead."
)


def _resolve_account_id(
    account_id_cookie: Optional[str],
    user_token: Optional[str],
) -> Optional[int]:
    if account_id_cookie:
        try:
            return int(account_id_cookie)
        except ValueError:
            pass
    if user_token:
        session = _session_adapter.find_by_token(user_token)
        if session:
            try:
                return int(session.user_id)
            except ValueError:
                pass
    return None


@router.post("/decision")
async def legacy_decision_disabled():
    raise HTTPException(status_code=410, detail=_DISABLED_DECISION_DETAIL)


@router.post("/decision/stream")
async def legacy_decision_stream_disabled():
    raise HTTPException(status_code=410, detail=_DISABLED_DECISION_DETAIL)


@router.post("/youtube-sentiment", response_model=YouTubeSentimentResponse)
async def youtube_sentiment_analysis(
    request: YouTubeSentimentRequest,
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    """Summarize saved YouTube comment sentiment for a logged-in account."""
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="Login required")

    try:
        adapter = YouTubeSentimentAdapter()
        usecase = YouTubeSentimentUseCase(adapter)
        metrics = await usecase.execute(company=request.company, log_id=request.log_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sd = metrics.get("sentiment_distribution", {})
    return YouTubeSentimentResponse(
        sentiment_distribution=SentimentDistribution(
            positive=sd.get("positive", 0.0),
            neutral=sd.get("neutral", 1.0),
            negative=sd.get("negative", 0.0),
        ),
        sentiment_score=metrics.get("sentiment_score", 0.0),
        bullish_keywords=metrics.get("bullish_keywords", []),
        bearish_keywords=metrics.get("bearish_keywords", []),
        topics=metrics.get("topics", []),
        volume=metrics.get("volume", 0),
    )
