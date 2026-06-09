import asyncio
import json

import httpx

from app.domains.stock_analyzer.adapter.outbound.external.acp_analyzer_adapter import ACPAnalyzerAdapter
from app.domains.stock_analyzer.domain.entity.analyzed_article import AnalyzedArticle


def test_acp_analyzer_posts_openai_compatible_json_request():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        content = json.dumps(
            {
                "summary": "factual summary",
                "tags": [{"label": "earnings", "category": "EARNINGS"}],
                "sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "confidence": 0.72,
            }
        )
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_acp_test",
                "object": "chat.completion",
                "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}],
            },
        )

    adapter = ACPAnalyzerAdapter(
        base_url="http://acp.local",
        api_key="secret",
        model="stock-summary-default",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        adapter.analyze(
            article_id="article-1",
            title="Samsung earnings update",
            body="Revenue improved.",
            category="NEWS",
        )
    )

    assert result.article_id == "article-1"
    assert result.summary == "factual summary"
    assert result.sentiment == "NEUTRAL"
    assert result.tags[0].category.value == "EARNINGS"

    sent = requests[0]
    assert sent.method == "POST"
    assert str(sent.url) == "http://acp.local/v1/chat/completions"
    assert sent.headers["authorization"] == "Bearer secret"

    body = json.loads(sent.content)
    assert body["model"] == "stock-summary-default"
    assert body["stream"] is False
    assert body["response_format"] == {"type": "json_object"}
    assert body["metadata"]["project"] == "alpha-desk"
    assert body["metadata"]["task"] == "stock-summary"
    assert body["metadata"]["article_id"] == "article-1"


def test_acp_analyzer_falls_back_when_content_is_not_json_object():
    class FallbackAnalyzer:
        async def analyze(self, article_id: str, title: str, body: str, category: str) -> AnalyzedArticle:
            return AnalyzedArticle(
                article_id=article_id,
                summary="fallback summary",
                tags=[],
                sentiment="NEUTRAL",
                sentiment_score=0.0,
                confidence=0.5,
                analyzer_version="fallback",
            )

        async def synthesize_articles(self, symbol: str, name: str, articles: list[dict]) -> AnalyzedArticle:
            return AnalyzedArticle(
                article_id=f"synthesis_{symbol}",
                summary="fallback synthesis",
                tags=[],
                sentiment="NEUTRAL",
                sentiment_score=0.0,
                confidence=0.5,
                analyzer_version="fallback",
            )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "not json"}}],
            },
        )

    adapter = ACPAnalyzerAdapter(
        base_url="http://acp.local",
        api_key="",
        model="stock-summary-default",
        fallback_adapter=FallbackAnalyzer(),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(adapter.analyze("article-2", "title", "body", "NEWS"))

    assert result.summary.startswith("[ACP 모델 출력 품질 기준 미달 - OpenAI fallback 사용]")
    assert "기사 원문 길이가 부족하다는 뜻이 아니라" in result.summary
    assert "Ollama 로컬 모델의 JSON 분석 안정성 문제" in result.summary
    assert "not json" in result.summary
    assert "[OpenAI 분석]\nfallback summary" in result.summary
    assert result.analyzer_version == "fallback+acp-fallback"


def test_acp_analyzer_falls_back_when_summary_is_empty():
    class FallbackAnalyzer:
        async def analyze(self, article_id: str, title: str, body: str, category: str) -> AnalyzedArticle:
            return AnalyzedArticle(
                article_id=article_id,
                summary="fallback non-empty summary",
                tags=[],
                sentiment="NEUTRAL",
                sentiment_score=0.0,
                confidence=0.5,
                analyzer_version="fallback",
            )

        async def synthesize_articles(self, symbol: str, name: str, articles: list[dict]) -> AnalyzedArticle:
            return AnalyzedArticle(
                article_id=f"synthesis_{symbol}",
                summary="fallback synthesis",
                tags=[],
                sentiment="NEUTRAL",
                sentiment_score=0.0,
                confidence=0.5,
                analyzer_version="fallback",
            )

    def handler(request: httpx.Request) -> httpx.Response:
        content = json.dumps(
            {
                "summary": "",
                "tags": [],
                "sentiment": "NEUTRAL",
                "sentiment_score": 0.0,
                "confidence": 0.7,
            }
        )
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": content}}],
            },
        )

    adapter = ACPAnalyzerAdapter(
        base_url="http://acp.local",
        api_key="",
        model="stock-summary-default",
        fallback_adapter=FallbackAnalyzer(),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(adapter.analyze("article-3", "title", "body", "NEWS"))

    assert result.summary.startswith("[ACP 모델 출력 품질 기준 미달 - OpenAI fallback 사용]")
    assert "기사 원문 길이가 부족하다는 뜻이 아니라" in result.summary
    assert "Ollama 로컬 모델의 JSON 분석 안정성 문제" in result.summary
    assert "non-empty summary" in result.summary
    assert "[OpenAI 분석]\nfallback non-empty summary" in result.summary
    assert result.analyzer_version == "fallback+acp-fallback"


def test_acp_analyzer_fallback_summary_includes_gateway_rejected_content():
    class FallbackAnalyzer:
        async def analyze(self, article_id: str, title: str, body: str, category: str) -> AnalyzedArticle:
            return AnalyzedArticle(
                article_id=article_id,
                summary="openai fallback summary",
                tags=[],
                sentiment="NEUTRAL",
                sentiment_score=0.0,
                confidence=0.5,
                analyzer_version="fallback",
            )

        async def synthesize_articles(self, symbol: str, name: str, articles: list[dict]) -> AnalyzedArticle:
            return AnalyzedArticle(
                article_id=f"synthesis_{symbol}",
                summary="openai fallback synthesis",
                tags=[],
                sentiment="NEUTRAL",
                sentiment_score=0.0,
                confidence=0.5,
                analyzer_version="fallback",
            )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            502,
            json={
                "error": "Model profile requires summary to be at least 20 characters.",
                "rejectedContent": "{\"summary\":\"짧음\",\"tags\":[]}",
            },
        )

    adapter = ACPAnalyzerAdapter(
        base_url="http://acp.local",
        api_key="",
        model="stock-summary-default",
        fallback_adapter=FallbackAnalyzer(),
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(adapter.analyze("article-4", "title", "body", "NEWS"))

    assert "모델 출력 품질 기준 미달" in result.summary
    assert "기사 원문 길이가 부족하다는 뜻이 아니라" in result.summary
    assert "Ollama 로컬 모델의 JSON 분석 안정성 문제" in result.summary
    assert "requires summary" in result.summary
    assert "{\"summary\":\"짧음\",\"tags\":[]}" in result.summary
    assert "[OpenAI 분석]\nopenai fallback summary" in result.summary
