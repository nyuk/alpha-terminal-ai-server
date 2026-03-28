from typing import List, Optional, Tuple

import httpx

from app.domains.market_video.application.usecase.youtube_search_port import YoutubeSearchPort
from app.domains.market_video.domain.entity.youtube_video import YoutubeVideo
from app.infrastructure.config.settings import get_settings


class YoutubeSearchAdapter(YoutubeSearchPort):
    YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"
    PAGE_SIZE = 9

    def search(self, page_token: Optional[str], stock_name: Optional[str] = None) -> Tuple[List[YoutubeVideo], Optional[str], Optional[str], int]:
        settings = get_settings()
        keyword = f"{stock_name} 주식 분석" if stock_name else "주식 분석 종목"
        params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "maxResults": self.PAGE_SIZE,
            "key": settings.youtube_api_key,
            "relevanceLanguage": "ko",
            "regionCode": "KR",
            "order": "relevance",
        }
        if page_token:
            params["pageToken"] = page_token

        response = httpx.get(self.YOUTUBE_API_URL, params=params, timeout=10.0)

        if response.status_code == 403:
            error_reason = (
                response.json()
                .get("error", {})
                .get("errors", [{}])[0]
                .get("reason", "unknown")
            )
            raise PermissionError(f"YouTube API 접근 거부 (reason={error_reason}). "
                                  "Google Cloud Console에서 YouTube Data API v3 활성화 및 키 제한 설정을 확인하세요.")

        response.raise_for_status()
        data = response.json()

        items = data.get("items", [])
        next_token: Optional[str] = data.get("nextPageToken")
        prev_token: Optional[str] = data.get("prevPageToken")
        total: int = data.get("pageInfo", {}).get("totalResults", len(items))

        videos = [
            YoutubeVideo(
                title=item["snippet"]["title"],
                thumbnail_url=(
                    item["snippet"]["thumbnails"]
                    .get("high", item["snippet"]["thumbnails"].get("default", {}))
                    .get("url", "")
                ),
                channel_name=item["snippet"]["channelTitle"],
                published_at=item["snippet"]["publishedAt"],
                video_url=f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            )
            for item in items
        ]

        return videos, next_token, prev_token, total
