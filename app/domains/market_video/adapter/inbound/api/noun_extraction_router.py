from typing import Literal, Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.market_video.adapter.outbound.external.youtube_comment_adapter import YoutubeCommentAdapter
from app.domains.market_video.application.response.noun_frequency_response import NounFrequencyResponse
from app.domains.market_video.application.usecase.extract_nouns_usecase import ExtractNounsUseCase
from app.domains.market_video.infrastructure.orm.market_video_orm import MarketVideoORM
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db
from app.infrastructure.nlp.kiwi_morph_analyzer import KiwiMorphAnalyzer

router = APIRouter(prefix="/youtube", tags=["youtube"])

_session_adapter = RedisSessionAdapter(redis_client)


@router.get("/nouns", response_model=NounFrequencyResponse)
async def extract_nouns(
    order: Literal["relevance", "time"] = Query(default="relevance", description="댓글 정렬: relevance(인기순) | time(최신순)"),
    max_per_video: int = Query(default=20, ge=1, le=100, description="영상당 최대 수집 댓글 수"),
    top_n: int = Query(default=30, ge=1, le=200, description="반환할 상위 명사 개수"),
    user_token: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """market_videos에 저장된 영상의 댓글에서 명사를 추출하고 빈도순으로 반환한다."""
    if not user_token:
        raise HTTPException(status_code=401, detail="인증이 필요합니다.")
    session = _session_adapter.find_by_token(user_token)
    if session is None:
        raise HTTPException(status_code=401, detail="유효하지 않거나 만료된 세션입니다.")

    video_ids = [row.video_id for row in db.query(MarketVideoORM.video_id).all()]

    usecase = ExtractNounsUseCase(
        comment_port=YoutubeCommentAdapter(),
        morph_port=KiwiMorphAnalyzer(),
    )
    return usecase.execute(
        video_ids=video_ids,
        order=order,
        max_per_video=max_per_video,
        top_n=top_n,
    )
