from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.domains.account.adapter.outbound.persistence.account_repository_impl import AccountRepositoryImpl
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.kakao_auth.adapter.outbound.external.kakao_oauth_adapter import KakaoOAuthAdapter
from app.domains.kakao_auth.adapter.outbound.external.kakao_token_adapter import KakaoTokenAdapter
from app.domains.kakao_auth.adapter.outbound.in_memory.redis_temp_token_adapter import RedisTempTokenAdapter
from app.domains.kakao_auth.application.response.kakao_login_response import KakaoLoginResponse
from app.domains.kakao_auth.application.usecase.check_kakao_account_registration_usecase import CheckKakaoAccountRegistrationUseCase
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
        account_repository = AccountRepositoryImpl(db)
        usecase = CheckKakaoAccountRegistrationUseCase(
            token_port=_kakao_token_adapter,
            user_info_port=_kakao_token_adapter,
            account_repository=account_repository,
            temp_token_store=_temp_token_store,
        )
        result = usecase.execute(code)

        body = result.model_dump(exclude={"temp_token"})
        response = JSONResponse(content=body)

        if result.temp_token_issued and result.temp_token:
            response.set_cookie(
                key="temp_token",
                value=result.temp_token,
                httponly=True,
                max_age=300,
                samesite="lax",
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


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
