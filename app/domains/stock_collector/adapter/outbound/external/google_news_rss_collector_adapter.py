import datetime
import logging
from hashlib import sha256
from typing import List
from urllib.parse import quote
from xml.etree import ElementTree as ET

import httpx

from app.domains.stock_collector.application.usecase.collector_port import CollectorPort
from app.domains.stock_collector.domain.entity.raw_article import RawArticle

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; AlphaDesk/1.0)"}


class GoogleNewsRssCollectorAdapter(CollectorPort):
    BASE_URL = "https://news.google.com/rss/search"
    MAX_RESULTS = 10

    def collect(self, symbol: str, stock_name: str, corp_code: str) -> List[RawArticle]:
        query = quote(stock_name)
        url = f"{self.BASE_URL}?q={query}&hl=ko&gl=KR&ceid=KR:ko"

        try:
            response = httpx.get(url, headers=_HEADERS, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as e:
            logger.warning("[GoogleNewsRSS] 요청 실패: %s", e)
            return []

        try:
            root = ET.fromstring(response.text)
        except ET.ParseError as e:
            logger.warning("[GoogleNewsRSS] XML 파싱 실패: %s", e)
            return []

        items = root.findall(".//item")[: self.MAX_RESULTS]
        now = datetime.datetime.now().isoformat()
        articles = []

        for item in items:
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub_date = item.findtext("pubDate") or ""
            source = item.findtext("source") or "Google News"

            if not title or not link:
                continue

            content = title.encode()
            articles.append(
                RawArticle(
                    source_type="NEWS",
                    source_name="GOOGLE_NEWS_RSS",
                    source_doc_id=sha256(link.encode()).hexdigest()[:20],
                    url=link,
                    title=title,
                    body_text="",
                    published_at=pub_date,
                    collected_at=now,
                    symbol=symbol,
                    lang="ko",
                    content_hash=f"sha256:{sha256(content).hexdigest()}",
                    collector_version="collector-v1.0.0",
                    status="COLLECTED",
                    author=source,
                    meta={"query": stock_name},
                )
            )

        return articles
