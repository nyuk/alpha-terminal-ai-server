from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.domains.account.adapter.outbound.in_memory.redis_account_session_adapter import RedisAccountSessionAdapter
from app.domains.account.adapter.outbound.persistence.account_repository_impl import AccountRepositoryImpl
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.kakao_auth.adapter.outbound.external.kakao_oauth_adapter import KakaoOAuthAdapter
from app.domains.kakao_auth.adapter.outbound.external.kakao_token_adapter import KakaoTokenAdapter
from app.domains.kakao_auth.adapter.outbound.in_memory.redis_temp_token_adapter import RedisTempTokenAdapter
from app.domains.kakao_auth.application.response.kakao_login_response import KakaoLoginResponse
from app.domains.kakao_auth.application.usecase.check_kakao_user_registration_usecase import CheckKakaoUserRegistrationUseCase
from app.domains.kakao_auth.application.usecase.generate_kakao_oauth_url_usecase import GenerateKakaoOAuthUrlUseCase
from app.domains.kakao_auth.application.usecase.kakao_login_usecase import KakaoLoginUseCase
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/kakao-authentication", tags=["kakao-authentication"])

_settings = get_settings()

_kakao_oauth_adapter = KakaoOAuthAdapter(
    client_id=_settings.kakao_client_id,
    redirect_uri=_settings.kakao_redirect_uri,
)
_generate_url_usecase = GenerateKakaoOAuthUrlUseCase(_kakao_oauth_adapter)

_kakao_token_adapter = KakaoTokenAdapter(
    client_id=_settings.kakao_client_id,
    redirect_uri=_settings.kakao_redirect_uri,
)
_session_store = RedisSessionAdapter(redis_client)
_kakao_login_usecase = KakaoLoginUseCase(_kakao_token_adapter, _session_store)
_temp_token_store = RedisTempTokenAdapter(redis_client)
_account_session_adapter = RedisAccountSessionAdapter(redis_client)


@router.get("/request-oauth-link")
async def request_oauth_link():
    response = _generate_url_usecase.execute()
    return RedirectResponse(url=response.authorization_url)


@router.get("/request-access-token-after-redirection")
async def request_access_token_after_redirection(
    code: str = None,
    error: str = None,
    error_description: str = None,
    db: Session = Depends(get_db),
):
    if error:
        raise HTTPException(status_code=400, detail=f"Kakao OAuth error: {error} - {error_description}")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing")
    try:
        usecase = CheckKakaoUserRegistrationUseCase(
            token_port=_kakao_token_adapter,
            user_info_port=_kakao_token_adapter,
            account_repository=AccountRepositoryImpl(db),
            temp_token_store=_temp_token_store,
        )
        result = usecase.execute(code)

        # 기존 회원: 세션 발급 → Cookie → Redirect
        if result.is_registered and result.account_id and result.kakao_access_token:
            user_token = _account_session_adapter.create(result.account_id)
            _account_session_adapter.save_account_kakao_token(result.account_id, result.kakao_access_token)

            response = RedirectResponse(url=_settings.cors_allowed_frontend_url, status_code=302)
            response.set_cookie(
                key="user_token",
                value=user_token,
                httponly=True,
                max_age=3600,
                samesite="lax",
            )
            response.set_cookie(key="nickname", value=result.nickname, max_age=3600, samesite="lax")
            response.set_cookie(key="email", value=result.email, max_age=3600, samesite="lax")
            response.set_cookie(key="account_id", value=str(result.account_id), max_age=3600, samesite="lax")
            return response

        # 신규 회원: /auth-callback redirect + temp_token HttpOnly Cookie
        callback_url = (
            f"{_settings.cors_allowed_frontend_url}/auth-callback"
            f"?nickname={quote(result.nickname)}&email={quote(result.email)}"
        )
        response = RedirectResponse(url=callback_url, status_code=302)

        if result.temp_token_issued and result.temp_token:
            response.set_cookie(
                key="temp_token",
                value=result.temp_token,
                httponly=True,
                max_age=300,
                samesite="lax",
            )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Kakao request failed: {e}")


@router.get("/redirection", response_model=KakaoLoginResponse)
async def kakao_redirection(code: str = None, error: str = None, error_description: str = None):
    if error:
        raise HTTPException(status_code=400, detail=f"Kakao OAuth error: {error} - {error_description}")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code is missing")
    try:
        return _kakao_login_usecase.execute(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
