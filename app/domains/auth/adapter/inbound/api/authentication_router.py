from typing import Optional
from urllib.parse import unquote

from fastapi import APIRouter, Cookie, HTTPException

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.auth.adapter.outbound.in_memory.redis_temp_token_check_adapter import RedisTempTokenCheckAdapter
from app.domains.auth.application.response.me_response import MeResponse
from app.domains.auth.application.usecase.get_me_usecase import GetMeUseCase
from app.infrastructure.cache.redis_client import redis_client

router = APIRouter(prefix="/authentication", tags=["authentication"])

_session_adapter = RedisSessionAdapter(redis_client)
_temp_token_check = RedisTempTokenCheckAdapter(redis_client)
_get_me_usecase = GetMeUseCase(_session_adapter, _temp_token_check)


@router.get("/me", response_model=MeResponse)
async def get_me(
    user_token: Optional[str] = Cookie(default=None),
    temp_token: Optional[str] = Cookie(default=None),
    nickname: Optional[str] = Cookie(default=None),
    email: Optional[str] = Cookie(default=None),
    kakao_nickname: Optional[str] = Cookie(default=None),
    kakao_email: Optional[str] = Cookie(default=None),
):
    try:
        return _get_me_usecase.execute(
            user_token=user_token,
            temp_token=temp_token,
            nickname=unquote(nickname) if nickname else None,
            email=unquote(email) if email else None,
            kakao_nickname=unquote(kakao_nickname) if kakao_nickname else None,
            kakao_email=unquote(kakao_email) if kakao_email else None,
        )
    except PermissionError as e:
        raise HTTPException(status_code=401, detail=str(e))
