from app.domains.market_analysis.adapter.outbound.external.acp_market_analysis_qa_adapter import (
    ACPMarketAnalysisQAAdapter,
)
from app.domains.market_analysis.adapter.outbound.external.langchain_qa_adapter import LangChainQAAdapter
from app.domains.market_analysis.application.usecase.langchain_qa_port import LangChainQAPort
from app.infrastructure.config.settings import Settings, get_settings


def build_market_analysis_qa(settings: Settings | None = None) -> LangChainQAPort:
    resolved_settings = settings or get_settings()
    provider = resolved_settings.llm_provider.strip().lower()

    openai_adapter = LangChainQAAdapter(
        api_key=resolved_settings.openai_api_key,
        model=resolved_settings.openai_model,
    )

    if provider != "acp":
        return openai_adapter

    fallback_adapter = openai_adapter if resolved_settings.acp_fallback_openai else None
    return ACPMarketAnalysisQAAdapter(
        base_url=resolved_settings.acp_base_url,
        api_key=resolved_settings.acp_api_key,
        model=resolved_settings.acp_model,
        timeout_seconds=resolved_settings.acp_timeout_seconds,
        fallback_adapter=fallback_adapter,
    )
