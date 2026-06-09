import json

import httpx

from app.domains.market_analysis.adapter.outbound.external.acp_market_analysis_qa_adapter import (
    ACPMarketAnalysisQAAdapter,
)
from app.domains.market_analysis.domain.entity.analysis_answer import AnalysisAnswer


def test_acp_market_analysis_qa_posts_openai_compatible_request():
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl_acp_ai_briefing_test",
                "object": "chat.completion",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "결론: 보유 권고. 리스크를 확인하세요.",
                        },
                    }
                ],
            },
        )

    adapter = ACPMarketAnalysisQAAdapter(
        base_url="http://acp.local",
        api_key="secret",
        model="stock-summary-default",
        transport=httpx.MockTransport(handler),
    )

    result = adapter.ask("하이닉스 매수 추천해?", "관심종목: SK하이닉스")

    assert result.answer.startswith("결론: 보유 권고")
    assert result.in_scope is True

    sent = requests[0]
    assert sent.method == "POST"
    assert str(sent.url) == "http://acp.local/v1/chat/completions"
    assert sent.headers["authorization"] == "Bearer secret"

    body = json.loads(sent.content)
    assert body["model"] == "stock-summary-default"
    assert body["stream"] is False
    assert body["metadata"]["project"] == "alpha-desk"
    assert body["metadata"]["task"] == "ai-briefing"
    assert body["messages"][0]["role"] == "system"
    assert "관심종목: SK하이닉스" in body["messages"][0]["content"]
    assert body["messages"][1] == {"role": "user", "content": "하이닉스 매수 추천해?"}


def test_acp_market_analysis_qa_falls_back_on_gateway_error():
    class FallbackQA:
        def ask(self, question: str, context: str) -> AnalysisAnswer:
            return AnalysisAnswer(answer=f"fallback: {question}", in_scope=True)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="gateway unavailable")

    adapter = ACPMarketAnalysisQAAdapter(
        base_url="http://acp.local",
        api_key="",
        model="stock-summary-default",
        fallback_adapter=FallbackQA(),
        transport=httpx.MockTransport(handler),
    )

    result = adapter.ask("삼성전자 보유?", "관심종목: 삼성전자")

    assert result.answer == "fallback: 삼성전자 보유?"
    assert result.in_scope is True
