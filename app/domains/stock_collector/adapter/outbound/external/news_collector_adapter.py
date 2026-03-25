import logging
import time
from datetime import datetime
from hashlib import sha256
from typing import List

import httpx

from app.domains.stock_collector.application.usecase.collector_port import CollectorPort
from app.domains.stock_collector.domain.entity.raw_article import RawArticle
from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


class NewsCollectorAdapter(CollectorPort):
    SERP_API_URL = "https://serpapi.com/search"

    def collect(self, symbol: str, stock_name: str, corp_code: str) -> List[RawArticle]:
        settings = get_settings()

        params = {
            "engine": "google_news",
            "q": stock_name,
            "api_key": settings.serp_api_key,
            "num": "10",
        }

        try:
            time.sleep(1)
            response = httpx.get(self.SERP_API_URL, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.warning(f"[NewsCollector] SerpAPI 요청 실패: {e}")
            return []

        articles = []
        now = datetime.now().isoformat()

        for item in data.get("news_results", []):
            link = item.get("link", "")
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            content = f"{title}{snippet}".encode()

            articles.append(
                RawArticle(
                    source_type="NEWS",
                    source_name="GOOGLE_NEWS",
                    source_doc_id=sha256(link.encode()).hexdigest()[:20],
                    url=link,
                    title=title,
                    body_text=snippet,
                    published_at=item.get("date", ""),
                    collected_at=now,
                    symbol=symbol,
                    content_hash=f"sha256:{sha256(content).hexdigest()}",
                    collector_version="collector-v1.0.0",
                    status="COLLECTED",
                    author=item.get("source", {}).get("name", ""),
                    meta={
                        "press": item.get("source", {}).get("name", ""),
                    },
                )
            )

        return articles
