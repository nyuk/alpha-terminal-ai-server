import datetime
import logging
import re
from hashlib import sha256
from html import unescape
from typing import List

import httpx

from app.domains.stock_collector.application.usecase.collector_port import CollectorPort
from app.domains.stock_collector.domain.entity.raw_article import RawArticle
from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _clean(text: str) -> str:
    return unescape(_TAG_RE.sub("", text)).strip()


class NaverBlogCafeCollectorAdapter(CollectorPort):
    NEWS_URL = "https://openapi.naver.com/v1/search/news.json"
    MAX_RESULTS = 10

    def __init__(self):
        settings = get_settings()
        if not settings.naver_client_id or not settings.naver_secret:
            raise ValueError("NAVER_CLIENT_ID / NAVER_SECRET 환경변수가 설정되지 않았습니다.")
        self._headers = {
            "X-Naver-Client-Id": settings.naver_client_id,
            "X-Naver-Client-Secret": settings.naver_secret,
        }

    def collect(self, symbol: str, stock_name: str, corp_code: str) -> List[RawArticle]:
        return self._fetch(self.NEWS_URL, "NAVER_NEWS_API", symbol, stock_name)

    def _fetch(self, url: str, source_name: str, symbol: str, stock_name: str) -> List[RawArticle]:
        try:
            response = httpx.get(
                url,
                params={"query": stock_name, "display": self.MAX_RESULTS, "sort": "date"},
                headers=self._headers,
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("[%s] 요청 실패: %s", source_name, e)
            return []

        items = response.json().get("items", [])
        now = datetime.datetime.now().isoformat()
        articles = []

        for item in items:
            title = _clean(item.get("title", ""))
            link = item.get("link") or item.get("url", "")
            pub_date = item.get("pubDate") or item.get("postdate", "")
            description = _clean(item.get("description", ""))
            author = item.get("originallink") or item.get("cafename", "")

            if not title or not link:
                continue

            content = title.encode()
            articles.append(
                RawArticle(
                    source_type="NEWS",
                    source_name=source_name,
                    source_doc_id=sha256(link.encode()).hexdigest()[:20],
                    url=link,
                    title=title,
                    body_text=description,
                    published_at=pub_date,
                    collected_at=now,
                    symbol=symbol,
                    lang="ko",
                    content_hash=f"sha256:{sha256(content).hexdigest()}",
                    collector_version="collector-v1.0.0",
                    status="COLLECTED",
                    author=author,
                    meta={"query": stock_name},
                )
            )

        return articles
