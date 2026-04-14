"""투자 워크플로우 로그 컨텍스트 — 요청별 로그 큐를 contextvars로 관리한다.

사용 패턴:
    router: token = set_log_queue(q), asyncio.create_task(workflow)
    nodes:  await aemit("메시지")  → print + q.put
"""
import asyncio
from contextvars import ContextVar
from typing import Optional

_log_queue: ContextVar[Optional[asyncio.Queue]] = ContextVar(
    "investment_log_queue", default=None
)


def set_log_queue(q: asyncio.Queue):
    """현재 컨텍스트에 로그 큐를 등록한다. 반환값은 reset에 사용한다."""
    return _log_queue.set(q)


def reset_log_queue(token) -> None:
    """set_log_queue 호출 전 상태로 복원한다."""
    _log_queue.reset(token)


async def aemit(message: str) -> None:
    """로그 메시지를 콘솔에 출력하고 SSE 큐에 전송한다.

    큐가 없으면 print만 실행한다 (SSE 없이 직접 호출 시 하위 호환).
    """
    print(message)
    q = _log_queue.get()
    if q is not None:
        await q.put({"type": "log", "data": message})
