from datetime import datetime, timedelta

from app.domains.stock_collector.application.usecase.collect_articles_usecase import CollectArticlesUseCase
from app.domains.stock_collector.domain.entity.raw_article import RawArticle


class FakeRawArticleRepository:
    def __init__(self, articles=None):
        self.articles = articles or []

    def save(self, article):
        self.articles.append(article)
        return article

    def find_by_dedup_key(self, source_type, source_doc_id):
        return next(
            (
                article
                for article in self.articles
                if article.source_type == source_type and article.source_doc_id == source_doc_id
            ),
            None,
        )

    def find_all(self, symbol=None, source_type=None):
        return [
            article
            for article in self.articles
            if (symbol is None or article.symbol == symbol)
            and (source_type is None or article.source_type == source_type)
        ]

    def migrate_symbol(self, old_symbol, new_symbol):
        return 0


class CountingCollector:
    def __init__(self, articles=None):
        self.calls = 0
        self.articles = articles or []

    def collect(self, symbol, stock_name, corp_code):
        self.calls += 1
        return self.articles


def _article(source_type, source_doc_id, symbol="005930", created_at=None):
    return RawArticle(
        source_type=source_type,
        source_name="TEST",
        source_doc_id=source_doc_id,
        url=f"https://example.com/{source_doc_id}",
        title=f"{source_doc_id} title",
        body_text="body",
        published_at="20260506",
        collected_at=(created_at or datetime.now()).isoformat(),
        symbol=symbol,
        content_hash=f"sha256:{source_doc_id}",
        collector_version="test",
        status="COLLECTED",
        created_at=created_at or datetime.now(),
    )


def _settings_env(monkeypatch, fresh_minutes="360"):
    monkeypatch.setenv("MYSQL_USER", "test")
    monkeypatch.setenv("MYSQL_PASSWORD", "test")
    monkeypatch.setenv("MYSQL_HOST", "localhost")
    monkeypatch.setenv("MYSQL_PORT", "3306")
    monkeypatch.setenv("MYSQL_DATABASE", "test")
    monkeypatch.setenv("PIPELINE_COLLECTION_FRESH_MINUTES", fresh_minutes)


def test_execute_reuses_recent_kr_news_and_report_collection(monkeypatch):
    _settings_env(monkeypatch)
    repo = FakeRawArticleRepository([
        _article("NEWS", "news-1"),
        _article("DISCLOSURE", "dart-1"),
    ])
    collector = CountingCollector([_article("NEWS", "news-2")])

    result = CollectArticlesUseCase(repo, [collector]).execute("005930")

    assert collector.calls == 0
    assert result.total_collected == 0
    assert result.total_skipped == 2


def test_execute_collects_when_recent_report_is_missing_for_kr_stock(monkeypatch):
    _settings_env(monkeypatch)
    repo = FakeRawArticleRepository([_article("NEWS", "news-1")])
    collector = CountingCollector([_article("DISCLOSURE", "dart-1")])

    result = CollectArticlesUseCase(repo, [collector]).execute("005930")

    assert collector.calls == 1
    assert result.total_collected == 1


def test_execute_collects_when_existing_articles_are_stale(monkeypatch):
    _settings_env(monkeypatch, fresh_minutes="60")
    stale_time = datetime.now() - timedelta(hours=2)
    repo = FakeRawArticleRepository([
        _article("NEWS", "news-1", created_at=stale_time),
        _article("DISCLOSURE", "dart-1", created_at=stale_time),
    ])
    collector = CountingCollector([_article("NEWS", "news-2")])

    result = CollectArticlesUseCase(repo, [collector]).execute("005930")

    assert collector.calls == 1
    assert result.total_collected == 1
