import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter import OpenAIAnalyzerAdapter


@patch("app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter.AsyncOpenAI")
def test_openai_analyzer_uses_configured_model_and_json_response_format(mock_openai_cls):
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(
                content=json.dumps(
                    {
                        "summary": "direct summary",
                        "tags": [{"label": "earnings", "category": "EARNINGS"}],
                        "sentiment": "NEUTRAL",
                        "sentiment_score": 0.0,
                        "confidence": 0.8,
                    }
                )
            )
        )
    ]
    create = AsyncMock(return_value=response)
    mock_client = MagicMock()
    mock_client.chat.completions.create = create
    mock_openai_cls.return_value = mock_client

    adapter = OpenAIAnalyzerAdapter(api_key="sk-test", model="gpt-test")
    result = asyncio.run(adapter.analyze("article-1", "title", "body", "NEWS"))

    assert result.summary == "direct summary"
    create.assert_awaited_once()
    kwargs = create.await_args.kwargs
    assert kwargs["model"] == "gpt-test"
    assert kwargs["response_format"] == {"type": "json_object"}


@patch("app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter.AsyncOpenAI")
def test_openai_analyzer_treats_unknown_tag_category_as_other(mock_openai_cls):
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(
                content=json.dumps(
                    {
                        "summary": "summary",
                        "tags": [{"label": "unexpected", "category": "NOT_A_CATEGORY"}],
                        "sentiment": "NEUTRAL",
                        "sentiment_score": 0.0,
                        "confidence": 0.7,
                    }
                )
            )
        )
    ]
    create = AsyncMock(return_value=response)
    mock_client = MagicMock()
    mock_client.chat.completions.create = create
    mock_openai_cls.return_value = mock_client

    adapter = OpenAIAnalyzerAdapter(api_key="sk-test", model="gpt-test")
    result = asyncio.run(adapter.analyze("article-1", "title", "body", "NEWS"))

    assert result.tags[0].category.value == "OTHER"


@patch("app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter.AsyncOpenAI")
def test_openai_analyzer_rejects_empty_summary(mock_openai_cls):
    response = MagicMock()
    response.choices = [
        MagicMock(
            message=MagicMock(
                content=json.dumps(
                    {
                        "summary": "",
                        "tags": [],
                        "sentiment": "NEUTRAL",
                        "sentiment_score": 0.0,
                        "confidence": 0.7,
                    }
                )
            )
        )
    ]
    create = AsyncMock(return_value=response)
    mock_client = MagicMock()
    mock_client.chat.completions.create = create
    mock_openai_cls.return_value = mock_client

    adapter = OpenAIAnalyzerAdapter(api_key="sk-test", model="gpt-test")

    with pytest.raises(RuntimeError, match="non-empty summary"):
        asyncio.run(adapter.analyze("article-1", "title", "body", "NEWS"))
