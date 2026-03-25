import logging
from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.domains.account.adapter.outbound.in_memory.redis_account_session_adapter import RedisAccountSessionAdapter
from app.domains.account.adapter.outbound.in_memory.redis_kakao_token_adapter import RedisKakaoTokenAdapter
from app.domains.account.adapter.outbound.in_memory.redis_temp_token_port_impl import RedisTempTokenPortImpl
from app.domains.account.adapter.outbound.persistence.account_repository_impl import AccountRepositoryImpl
from app.domains.account.application.request.register_account_request import RegisterAccountRequest
from app.domains.account.application.usecase.logout_account_usecase import LogoutAccountUseCase
from app.domains.account.application.usecase.register_account_usecase import (
    AccountLinkConflictError,
    RegisterAccountUseCase,
)
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])

_settings = get_settings()

_temp_token_port = RedisTempTokenPortImpl(redis_client)
_kakao_token_store = RedisKakaoTokenAdapter(redis_client)
_session_store = RedisAccountSessionAdapter(redis_client)


@router.post("/register")
async def register_account(
    request: RegisterAccountRequest,
    temp_token: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not temp_token:
        raise HTTPException(status_code=401, detail="임시 토큰이 없습니다.")

    try:
        account_repository = AccountRepositoryImpl(db)
        usecase = RegisterAccountUseCase(
            account_repository=account_repository,
            temp_token_port=_temp_token_port,
            kakao_token_store=_kakao_token_store,
            session_store=_session_store,
        )
        result = usecase.execute(temp_token, request)

        frontend_url = _settings.cors_allowed_frontend_url
        response = JSONResponse(content={"success": True, "redirect_url": frontend_url})
        response.set_cookie(key="session_token", value=result.session_token, httponly=True, max_age=3600 * 24 * 7, samesite="lax")
        response.set_cookie(key="nickname", value=quote(result.nickname), max_age=3600 * 24 * 7, samesite="lax")
        response.set_cookie(key="email", value=quote(result.email), max_age=3600 * 24 * 7, samesite="lax")
        response.set_cookie(key="account_id", value=str(result.account_id), max_age=3600 * 24 * 7, samesite="lax")
        response.delete_cookie("temp_token")
        return response

    except AccountLinkConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.exception("회원가입 처리 중 오류 발생")
        raise HTTPException(status_code=400, detail="내부 오류가 발생했습니다.")


@router.post("/logout")
async def logout_account(
    session_token: str = Cookie(default=None),
    user_token: str = Cookie(default=None),
):
    token = session_token or user_token
    if not token:
        raise HTTPException(status_code=401, detail="로그인 상태가 아닙니다.")

    usecase = LogoutAccountUseCase(session_port=_session_store)
    usecase.execute(token)

    response = JSONResponse(content={"message": "로그아웃 되었습니다."})
    response.delete_cookie("session_token")
    response.delete_cookie("user_token")
    response.delete_cookie("nickname")
    response.delete_cookie("email")
    response.delete_cookie("account_id")
    return response
