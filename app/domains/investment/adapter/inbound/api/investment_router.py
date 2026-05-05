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

router = APIRouter(prefix="/investment", tags=["investment"])

_session_adapter = RedisSessionAdapter(redis_client)


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


_DISABLED_DECISION_DETAIL = (
    "투자 판단 API는 개인 프로젝트 전환 과정에서 비활성화되었습니다. "
    "관심종목 뉴스, 공시, 리포트의 사실 기반 요약과 리스크 브리핑만 제공합니다."
)


@router.post("/decision")
async def investment_decision():
    raise HTTPException(status_code=410, detail=_DISABLED_DECISION_DETAIL)


@router.post("/decision/stream")
async def investment_decision_stream():
    raise HTTPException(status_code=410, detail=_DISABLED_DECISION_DETAIL)


@router.post("/youtube-sentiment", response_model=YouTubeSentimentResponse)
async def youtube_sentiment_analysis(
    request: YouTubeSentimentRequest,
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    """저장된 YouTube 댓글로 투자 심리 지표를 산출한다.

    - company: 종목명으로 최근 수집 댓글 조회 (예: "삼성전자")
    - log_id : investment_youtube_logs.id로 특정 수집 세션 댓글 조회

    둘 중 하나는 반드시 지정해야 한다. log_id 가 지정되면 company 보다 우선한다.
    """
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

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
