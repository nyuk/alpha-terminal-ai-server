import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Cookie, HTTPException
from fastapi.responses import StreamingResponse

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.investment.adapter.outbound.agent import log_context
from app.domains.investment.adapter.outbound.external.langgraph_investment_adapter import LangGraphInvestmentAdapter
from app.domains.investment.application.request.investment_decision_request import InvestmentDecisionRequest
from app.domains.investment.application.response.investment_decision_response import InvestmentDecisionResponse
from app.domains.investment.application.usecase.investment_decision_usecase import InvestmentDecisionUseCase
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
    """인증된 사용자의 투자 판단 질의를 LangGraph 멀티 에이전트로 처리한다."""
    aid = _resolve_account_id(account_id, user_token)
    if aid is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

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
