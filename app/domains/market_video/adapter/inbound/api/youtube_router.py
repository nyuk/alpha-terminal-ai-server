from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.market_video.adapter.outbound.persistence.market_video_repository_impl import (
    MarketVideoRepositoryImpl,
)
from app.domains.market_video.application.response.youtube_video_list_response import YoutubeVideoListResponse
from app.domains.market_video.application.usecase.get_youtube_video_list_usecase import GetYoutubeVideoListUseCase
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/youtube", tags=["youtube"])

_session_adapter = RedisSessionAdapter(redis_client)


@router.get("/list", response_model=YoutubeVideoListResponse)
async def get_youtube_video_list(
    stock_name: Optional[str] = Query(default=None, description="검색할 관심종목 이름"),
    page_token: Optional[str] = Query(default=None, description="페이지 번호 (1부터 시작)"),
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """market_videos DB에서 영상 목록을 조회한다. YouTube API를 호출하지 않는다."""
    if not user_token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    session = _session_adapter.find_by_token(user_token)
    if session is None:
        raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 세션입니다.")

    usecase = GetYoutubeVideoListUseCase(MarketVideoRepositoryImpl(db))
    return usecase.execute(page_token, stock_name)
