from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.analytics.application.request.record_event_request import RecordEventRequest
from app.domains.analytics.application.usecase.record_event_usecase import RecordEventUseCase
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])

_session_adapter = RedisSessionAdapter(redis_client)


def _resolve_account_id(
    session_token: Optional[str],
    user_token: Optional[str],
) -> int:
    token = session_token or user_token
    if not token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    session = _session_adapter.find_by_token(token)
    if not session:
        raise HTTPException(status_code=401, detail="세션이 만료되었습니다.")
    return int(session.user_id)


@router.post("/event", status_code=204)
def record_event(
    body: RecordEventRequest,
    session_token: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
) -> None:
    account_id = _resolve_account_id(session_token, user_token)
    RecordEventUseCase(db).execute(account_id, body.event_type, body.campaign)
