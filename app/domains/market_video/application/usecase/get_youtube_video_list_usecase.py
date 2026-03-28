from typing import Optional

from app.domains.market_video.application.response.youtube_video_list_response import (
    YoutubeVideoItem,
    YoutubeVideoListResponse,
)
from app.domains.market_video.application.usecase.market_video_repository_port import MarketVideoRepositoryPort

PAGE_SIZE = 9


class GetYoutubeVideoListUseCase:
    """YouTube API를 호출하지 않고 market_videos DB에서 읽어 반환한다.
    할당량 소모 없이 저장된 데이터를 페이지네이션하여 제공한다."""

    def __init__(self, repository: MarketVideoRepositoryPort):
        self._repository = repository

    def execute(
        self,
        page_token: Optional[str],
        stock_name: Optional[str] = None,
    ) -> YoutubeVideoListResponse:
        page = int(page_token) if page_token and page_token.isdigit() else 1

        videos, total = self._repository.find_paginated(
            page=page,
            page_size=PAGE_SIZE,
            stock_name=stock_name,
        )

        total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
        next_token = str(page + 1) if page < total_pages else None
        prev_token = str(page - 1) if page > 1 else None

        return YoutubeVideoListResponse(
            items=[
                YoutubeVideoItem(
                    title=v.title,
                    thumbnail_url=v.thumbnail_url,
                    channel_name=v.channel_name,
                    published_at=v.published_at.isoformat(),
                    video_url=v.video_url,
                )
                for v in videos
            ],
            next_page_token=next_token,
            prev_page_token=prev_token,
            total_results=total,
        )
