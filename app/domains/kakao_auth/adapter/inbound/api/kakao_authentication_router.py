import logging
import secrets
from urllib.parse import quote

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.domains.account.adapter.outbound.in_memory.redis_account_session_adapter import RedisAccountSessionAdapter
from app.domains.account.adapter.outbound.in_memory.redis_kakao_token_adapter import RedisKakaoTokenAdapter
from app.domains.account.adapter.outbound.persistence.account_repository_impl import AccountRepositoryImpl
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.kakao_auth.adapter.outbound.external.kakao_oauth_adapter import KakaoOAuthAdapter
from app.domains.kakao_auth.adapter.outbound.external.kakao_token_adapter import KakaoTokenAdapter
from app.domains.kakao_auth.adapter.outbound.in_memory.redis_temp_token_adapter import (
    RedisTempTokenAdapter,
    TEMP_TOKEN_TTL_SECONDS,
)
from app.domains.kakao_auth.application.response.kakao_login_response import KakaoLoginResponse
from app.domains.kakao_auth.application.usecase.check_kakao_user_registration_usecase import CheckKakaoUserRegistrationUseCase
from app.domains.kakao_auth.application.usecase.kakao_login_usecase import KakaoLoginUseCase
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/kakao-authentication", tags=["kakao-authentication"])

_settings = get_settings()

_session_store = RedisSessionAdapter(redis_client)
_temp_token_store = RedisTempTokenAdapter(redis_client)
_kakao_session_store = RedisAccountSessionAdapter(redis_client)
_kakao_token_link = RedisKakaoTokenAdapter(redis_client)


_OAUTH_STATE_TTL = 600  # 10분


def _require_kakao_token_adapter() -> KakaoTokenAdapter:
    if not _settings.kakao_client_id or not _settings.kakao_redirect_uri:
        raise HTTPException(status_code=503, detail="Kakao OAuth is not configured")
    return KakaoTokenAdapter(
        client_id=_settings.kakao_client_id,
        redirect_uri=_settings.kakao_redirect_uri,
    )


def _require_kakao_oauth_adapter() -> KakaoOAuthAdapter:
    if not _settings.kakao_client_id or not _settings.kakao_redirect_uri:
        raise HTTPException(status_code=503, detail="Kakao OAuth is not configured")
    return KakaoOAuthAdapter(
        client_id=_settings.kakao_client_id,
        redirect_uri=_settings.kakao_redirect_uri,
    )


@router.get("/request-oauth-link")
async def request_oauth_link():
    state = secrets.token_urlsafe(32)
    redis_client.setex(f"oauth_state:{state}", _OAUTH_STATE_TTL, "1")
    url = _require_kakao_oauth_adapter().generate(state=state)
    return RedirectResponse(url=url)


@router.get("/request-access-token-after-redirection")
async def request_access_token_after_redirection(
    code: str = None,
    state: str = None,
    error: str = None,
    error_description: str = None,
    db: Session = Depends(get_db),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Kakao OAuth error: {error} - {error_description}")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing")
    # CSRF 방지: state 검증
    if not state or not redis_client.getdel(f"oauth_state:{state}"):
        raise HTTPException(status_code=400, detail="유효하지 않은 state 파라미터입니다.")
    try:
        kakao_token_adapter = _require_kakao_token_adapter()
        usecase = CheckKakaoUserRegistrationUseCase(
            token_port=kakao_token_adapter,
            user_info_port=kakao_token_adapter,
            account_repository=AccountRepositoryImpl(db),
            temp_token_store=_temp_token_store,
            session_store=_kakao_session_store,
            kakao_token_link=_kakao_token_link,
        )
        result = usecase.execute(code)

        response = RedirectResponse(url=_settings.frontend_auth_callback_url)

        secure = _settings.cookie_secure
        if result.is_registered and result.user_token:
            response.set_cookie(key="user_token", value=result.user_token, httponly=True, secure=secure, max_age=3600 * 24 * 7, samesite="lax")
            response.set_cookie(key="nickname", value=quote(result.nickname), secure=secure, max_age=3600 * 24 * 7, samesite="lax")
            response.set_cookie(key="email", value=quote(result.email), secure=secure, max_age=3600 * 24 * 7, samesite="lax")
            response.set_cookie(key="account_id", value=str(result.account_id), secure=secure, max_age=3600 * 24 * 7, samesite="lax")

        if result.temp_token_issued and result.temp_token:
            response.set_cookie(
                key="temp_token",
                value=result.temp_token,
                httponly=True,
                secure=secure,
                max_age=TEMP_TOKEN_TTL_SECONDS,
                samesite="lax",
            )
            response.set_cookie(
                key="kakao_nickname",
                value=quote(result.nickname),
                secure=secure,
                max_age=TEMP_TOKEN_TTL_SECONDS,
                samesite="lax",
            )
            response.set_cookie(
                key="kakao_email",
                value=quote(result.email),
                secure=secure,
                max_age=TEMP_TOKEN_TTL_SECONDS,
                samesite="lax",
            )

        return response

    except ValueError as e:
        logger.warning("[KakaoAuth] 인증 처리 실패: %s", e)
        raise HTTPException(status_code=400, detail="인증 처리에 실패했습니다.")
    except Exception as e:
        logger.error("[KakaoAuth] 카카오 요청 오류", exc_info=True)
        raise HTTPException(status_code=502, detail="일시적 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")


@router.get("/redirection", response_model=KakaoLoginResponse)
async def kakao_redirection(code: str = None, error: str = None, error_description: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Kakao OAuth error: {error} - {error_description}")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing")
    try:
        usecase = KakaoLoginUseCase(_require_kakao_token_adapter(), _session_store)
        return usecase.execute(code)
    except Exception as e:
        logger.error("[KakaoRedirection] 로그인 처리 오류", exc_info=True)
        raise HTTPException(status_code=400, detail="로그인 처리에 실패했습니다.")
