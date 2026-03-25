import datetime
import logging
from hashlib import sha256
from typing import List

import tweepy

from app.domains.stock_collector.application.usecase.collector_port import CollectorPort
from app.domains.stock_collector.domain.entity.raw_article import RawArticle
from app.infrastructure.config.settings import get_settings

logger = logging.getLogger(__name__)


class TwitterCollectorAdapter(CollectorPort):
    MAX_RESULTS = 10

    def __init__(self):
        token = get_settings().twitter_bearer_token
        if not token:
            raise ValueError("TWITTER_BEARER_TOKEN 환경변수가 설정되지 않았습니다.")
        self._client = tweepy.Client(bearer_token=token, wait_on_rate_limit=False)

    def collect(self, symbol: str, stock_name: str, corp_code: str) -> List[RawArticle]:
        query = f'"{stock_name}" OR "${symbol}" -is:retweet lang:ko'

        try:
            response = self._client.search_recent_tweets(
                query=query,
                max_results=self.MAX_RESULTS,
                tweet_fields=["created_at", "author_id", "text"],
            )
        except tweepy.TweepyException as e:
            logger.warning("[TwitterCollector] API 요청 실패: %s", e)
            return []

        if not response.data:
            return []

        now = datetime.datetime.now().isoformat()
        articles = []

        for tweet in response.data:
            tweet_url = f"https://twitter.com/i/web/status/{tweet.id}"
            content = tweet.text.encode()
            published_at = tweet.created_at.isoformat() if tweet.created_at else ""

            articles.append(
                RawArticle(
                    source_type="TWITTER",
                    source_name="TWITTER_API_V2",
                    source_doc_id=str(tweet.id),
                    url=tweet_url,
                    title=tweet.text[:100],
                    body_text=tweet.text,
                    published_at=published_at,
                    collected_at=now,
                    symbol=symbol,
                    lang="ko",
                    content_hash=f"sha256:{sha256(content).hexdigest()}",
                    collector_version="collector-v1.0.0",
                    status="COLLECTED",
                    author=str(tweet.author_id),
                    meta={"query": query},
                )
            )

        return articles
