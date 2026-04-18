from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.user_profile.adapter.outbound.persistence.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)
from app.domains.user_profile.application.request.save_recently_viewed_request import SaveRecentlyViewedRequest
from app.domains.user_profile.application.response.user_profile_response import UserProfileResponse, SaveRecentlyViewedResponse
from app.domains.user_profile.application.usecase.get_user_profile_usecase import GetUserProfileUseCase
from app.domains.user_profile.application.usecase.save_recently_viewed_usecase import SaveRecentlyViewedUseCase
from app.domains.watchlist.adapter.outbound.persistence.watchlist_repository_impl import WatchlistRepositoryImpl
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/users", tags=["user-profile"])

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


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    requester_id = _resolve_account_id(account_id, user_token)
    if requester_id is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    if requester_id != user_id:
        raise HTTPException(status_code=403, detail="본인 프로필만 조회할 수 있습니다.")

    user_profile_repo = UserProfileRepositoryImpl(db)
    watchlist_repo = WatchlistRepositoryImpl(db)
    usecase = GetUserProfileUseCase(
        repository=user_profile_repo,
        watchlist_port=watchlist_repo,
    )
    return usecase.execute(account_id=user_id)


@router.post("/{user_id}/recently-viewed", response_model=SaveRecentlyViewedResponse)
async def save_recently_viewed(
    user_id: int,
    request: SaveRecentlyViewedRequest,
    db: Session = Depends(get_db),
    account_id: Optional[str] = Cookie(default=None),
    user_token: Optional[str] = Cookie(default=None),
):
    requester_id = _resolve_account_id(account_id, user_token)
    if requester_id is None:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    if requester_id != user_id:
        raise HTTPException(status_code=403, detail="본인 이력만 저장할 수 있습니다.")

    repo = UserProfileRepositoryImpl(db)
    usecase = SaveRecentlyViewedUseCase(repository=repo)
    return usecase.execute(account_id=user_id, request=request)
