from types import SimpleNamespace
from unittest.mock import patch

from app.domains.market_analysis.adapter.outbound.external.market_analysis_qa_factory import (
    build_market_analysis_qa,
)


def test_build_market_analysis_qa_defaults_to_openai_without_acp_dependency():
    settings = SimpleNamespace(
        llm_provider="openai",
        openai_api_key="sk-test",
        openai_model="gpt-test",
        acp_base_url="http://localhost:4100",
        acp_api_key="",
        acp_model="stock-summary-default",
        acp_timeout_seconds=8.0,
        acp_fallback_openai=True,
    )

    with (
        patch(
            "app.domains.market_analysis.adapter.outbound.external.market_analysis_qa_factory.LangChainQAAdapter"
        ) as mock_openai,
        patch(
            "app.domains.market_analysis.adapter.outbound.external.market_analysis_qa_factory.ACPMarketAnalysisQAAdapter"
        ) as mock_acp,
    ):
        qa = build_market_analysis_qa(settings)

    assert qa == mock_openai.return_value
    mock_openai.assert_called_once_with(api_key="sk-test", model="gpt-test")
    mock_acp.assert_not_called()


def test_build_market_analysis_qa_uses_acp_when_explicitly_selected():
    settings = SimpleNamespace(
        llm_provider="acp",
        openai_api_key="sk-test",
        openai_model="gpt-test",
        acp_base_url="http://acp.local",
        acp_api_key="secret",
        acp_model="stock-summary-default",
        acp_timeout_seconds=4.0,
        acp_fallback_openai=True,
    )

    with (
        patch(
            "app.domains.market_analysis.adapter.outbound.external.market_analysis_qa_factory.LangChainQAAdapter"
        ) as mock_openai,
        patch(
            "app.domains.market_analysis.adapter.outbound.external.market_analysis_qa_factory.ACPMarketAnalysisQAAdapter"
        ) as mock_acp,
    ):
        qa = build_market_analysis_qa(settings)

    assert qa == mock_acp.return_value
    mock_openai.assert_called_once_with(api_key="sk-test", model="gpt-test")
    mock_acp.assert_called_once_with(
        base_url="http://acp.local",
        api_key="secret",
        model="stock-summary-default",
        timeout_seconds=4.0,
        fallback_adapter=mock_openai.return_value,
    )
