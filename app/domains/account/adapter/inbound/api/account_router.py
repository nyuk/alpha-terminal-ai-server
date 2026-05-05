import logging
from urllib.parse import quote

from fastapi import APIRouter, Cookie, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domains.account.adapter.outbound.in_memory.redis_account_session_adapter import RedisAccountSessionAdapter
from app.domains.account.adapter.outbound.in_memory.redis_kakao_token_adapter import RedisKakaoTokenAdapter
from app.domains.account.adapter.outbound.in_memory.redis_temp_token_port_impl import RedisTempTokenPortImpl
from app.domains.account.adapter.outbound.persistence.account_repository_impl import AccountRepositoryImpl
from app.domains.account.application.request.register_account_request import RegisterAccountRequest
from app.domains.account.application.request.update_settings_request import UpdateSettingsRequest
from app.domains.account.application.response.account_settings_response import AccountSettingsResponse
from app.domains.account.application.usecase.logout_account_usecase import LogoutAccountUseCase
from app.domains.account.application.usecase.register_account_usecase import (
    AccountLinkConflictError,
    RegisterAccountUseCase,
)
from app.domains.account.infrastructure.orm.account_orm import AccountORM
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/account", tags=["account"])

_settings = get_settings()

_temp_token_port = RedisTempTokenPortImpl(redis_client)
_kakao_token_store = RedisKakaoTokenAdapter(redis_client)
_session_store = RedisAccountSessionAdapter(redis_client)

PERSONAL_KAKAO_ID = "local:stockbrief"
COOKIE_MAX_AGE = 3600 * 24 * 7


def _set_auth_cookies(
    response: JSONResponse,
    *,
    session_token: str,
    nickname: str,
    email: str,
    account_id: int,
    secure: bool,
) -> None:
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=secure,
        max_age=COOKIE_MAX_AGE,
        samesite="lax",
    )
    response.set_cookie(
        key="user_token",
        value=session_token,
        httponly=True,
        secure=secure,
        max_age=COOKIE_MAX_AGE,
        samesite="lax",
    )
    response.set_cookie(key="nickname", value=quote(nickname), secure=secure, max_age=COOKIE_MAX_AGE, samesite="lax")
    response.set_cookie(key="email", value=quote(email), secure=secure, max_age=COOKIE_MAX_AGE, samesite="lax")
    response.set_cookie(key="account_id", value=str(account_id), secure=secure, max_age=COOKIE_MAX_AGE, samesite="lax")


@router.post("/personal-login")
async def personal_login(db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.personal_auth_enabled:
        raise HTTPException(status_code=403, detail="Personal login is disabled.")

    email = (settings.personal_auth_email or "me@stockbrief.local").strip()
    nickname = (settings.personal_auth_nickname or "StockBrief User").strip()

    orm = (
        db.query(AccountORM)
        .filter(or_(AccountORM.kakao_id == PERSONAL_KAKAO_ID, AccountORM.email == email))
        .order_by(AccountORM.id.asc())
        .first()
    )
    if orm is None:
        orm = AccountORM(email=email, kakao_id=PERSONAL_KAKAO_ID, nickname=nickname, role="ADMIN")
        db.add(orm)
        db.commit()
        db.refresh(orm)
    else:
        changed = False
        if orm.kakao_id != PERSONAL_KAKAO_ID:
            orm.kakao_id = PERSONAL_KAKAO_ID
            changed = True
        if orm.email != email:
            orm.email = email
            changed = True
        if orm.nickname != nickname:
            orm.nickname = nickname
            changed = True
        if not orm.role:
            orm.role = "ADMIN"
            changed = True
        if changed:
            db.commit()
            db.refresh(orm)

    session_token = _session_store.create(account_id=int(orm.id), role=orm.role)
    frontend_url = settings.cors_allowed_frontend_url
    response = JSONResponse(
        content={
            "success": True,
            "redirect_url": frontend_url,
            "account_id": int(orm.id),
            "nickname": orm.nickname,
            "email": orm.email,
        }
    )
    _set_auth_cookies(
        response,
        session_token=session_token,
        nickname=orm.nickname,
        email=orm.email,
        account_id=int(orm.id),
        secure=settings.cookie_secure,
    )
    response.delete_cookie("temp_token")
    response.delete_cookie("kakao_nickname")
    response.delete_cookie("kakao_email")
    return response


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
            admin_secret_code=_settings.admin_secret_code,
        )
        result = usecase.execute(temp_token, request)

        frontend_url = _settings.cors_allowed_frontend_url
        secure = _settings.cookie_secure
        response = JSONResponse(content={"success": True, "redirect_url": frontend_url})
        _set_auth_cookies(
            response,
            session_token=result.session_token,
            nickname=result.nickname,
            email=result.email,
            account_id=result.account_id,
            secure=secure,
        )
        response.delete_cookie("temp_token")
        return response

    except AccountLinkConflictError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        logger.exception("회원가입 처리 중 오류 발생")
        raise HTTPException(status_code=400, detail="내부 오류가 발생했습니다.")


@router.get("/settings", response_model=AccountSettingsResponse)
async def get_account_settings(
    account_id: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    orm = db.query(AccountORM).filter(AccountORM.id == int(account_id)).first()
    if orm is None:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
    return AccountSettingsResponse(is_watchlist_public=bool(orm.is_watchlist_public))


@router.patch("/settings", response_model=AccountSettingsResponse)
async def update_account_settings(
    request: UpdateSettingsRequest,
    account_id: str = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    orm = db.query(AccountORM).filter(AccountORM.id == int(account_id)).first()
    if orm is None:
        raise HTTPException(status_code=404, detail="계정을 찾을 수 없습니다.")
    orm.is_watchlist_public = request.is_watchlist_public
    db.commit()
    return AccountSettingsResponse(is_watchlist_public=bool(orm.is_watchlist_public))


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
