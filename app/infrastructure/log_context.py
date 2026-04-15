"""공유 SSE 로그 컨텍스트 유틸리티.

각 도메인 워크플로우가 요청별 큐 없이도 호출 가능.
큐가 등록되어 있으면 SSE 스트림으로 전송하고, 없으면 print만 실행.
"""
import asyncio
from contextvars import ContextVar
from typing import Optional

_log_queue: ContextVar[Optional[asyncio.Queue]] = ContextVar(
    "shared_log_queue", default=None
)


def set_log_queue(q: asyncio.Queue):
    """현재 컨텍스트에 로그 큐를 등록한다."""
    return _log_queue.set(q)


def reset_log_queue(token) -> None:
    """set_log_queue 호출 전 상태로 복원한다."""
    _log_queue.reset(token)


async def aemit(message: str) -> None:
    """로그 메시지를 콘솔에 출력하고, 큐가 있으면 SSE 이벤트로 전송한다."""
    print(message)
    q = _log_queue.get()
    if q is not None:
        await q.put({"type": "log", "data": message})
