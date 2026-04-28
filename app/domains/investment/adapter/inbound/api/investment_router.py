import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import StreamingResponse

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.investment.adapter.outbound.agent import log_context
from app.domains.investment.adapter.outbound.external.langgraph_investment_adapter import LangGraphInvestmentAdapter
from app.domains.investment.adapter.outbound.external.youtube_sentiment_adapter import YouTubeSentimentAdapter
from app.domains.investment.application.request.investment_decision_request import InvestmentDecisionRequest
from app.domains.investment.application.request.youtube_sentiment_request import YouTubeSentimentRequest
from app.domains.investment.application.response.investment_decision_response import InvestmentDecisionResponse
from app.domains.investment.application.response.youtube_sentiment_response import (
    SentimentDistribution,
    YouTubeSentimentResponse,
)
from app.domains.investment.application.usecase.investment_decision_usecase import InvestmentDecisionUseCase
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


@router.post("/decision", response_model=InvestmentDecisionResponse)
async def investment_decision(
    request: InvestmentDecisionRequest,
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    """인증된 사용자의 투자 판단 질의를 LangGraph 멀티 에이전트로 처리한다.

    매 호출 시 새로 워크플로우를 실행하여 최신 데이터·관점을 반영한다.
    (2026-04-28 팀 결정: 동일 질문에 매번 다른 답을 허용하기로 함 — PG 분석 캐시 제거)
    """
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    if not request.symbol:
        raise HTTPException(status_code=422, detail="symbol 필드가 필요합니다.")

    adapter = LangGraphInvestmentAdapter()
    usecase = InvestmentDecisionUseCase(adapter)
    decision = await usecase.execute(query=request.query)

    return InvestmentDecisionResponse(answer=decision.answer)


@router.post("/decision/stream")
async def investment_decision_stream(
    request: InvestmentDecisionRequest,
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    """인증된 사용자의 투자 판단 질의를 SSE 스트림으로 처리한다.

    매 호출 시 새로 워크플로우를 실행한다 — 동일 질문에도 매번 새로운 분석을 제공.
    (2026-04-28 팀 결정: PG 분석 캐시 제거. LangChain LLM 캐시(5분)는 유지.)

    이벤트 유형:
        {"type": "log",    "data": "로그 메시지"}
        {"type": "result", "data": "최종 응답"}
        {"type": "error",  "data": "오류 메시지"}
        {"type": "end"}
    """
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    q: asyncio.Queue = asyncio.Queue(maxsize=2000)

    # 현재 컨텍스트에 큐 등록 → create_task 시 복사됨
    token = log_context.set_log_queue(q)

    async def _run_workflow():
        try:
            adapter = LangGraphInvestmentAdapter()
            usecase = InvestmentDecisionUseCase(adapter)
            decision = await usecase.execute(query=request.query)
            await q.put({"type": "result", "data": decision.answer})
        except Exception as e:
            await q.put({"type": "error", "data": str(e)})
        finally:
            await q.put({"type": "end"})

    # 백그라운드 태스크 — 현재 컨텍스트(큐 포함)를 복사하여 실행
    asyncio.create_task(_run_workflow())

    # 이 핸들러 컨텍스트에서는 큐 해제 (태스크는 복사본 보유)
    log_context.reset_log_queue(token)

    async def event_generator():
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=120.0)
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'error', 'data': '응답 타임아웃 (120s)'}, ensure_ascii=False)}\n\n"
                break

            yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"

            if msg["type"] in ("end", "error"):
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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
