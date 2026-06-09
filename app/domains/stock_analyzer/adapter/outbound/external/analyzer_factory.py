from app.domains.stock_analyzer.adapter.outbound.external.acp_analyzer_adapter import ACPAnalyzerAdapter
from app.domains.stock_analyzer.adapter.outbound.external.openai_analyzer_adapter import OpenAIAnalyzerAdapter
from app.domains.stock_analyzer.application.usecase.article_analyzer_port import ArticleAnalyzerPort
from app.infrastructure.config.settings import Settings, get_settings


def build_article_analyzer(settings: Settings | None = None) -> ArticleAnalyzerPort:
    resolved_settings = settings or get_settings()
    provider = resolved_settings.llm_provider.strip().lower()

    if provider != "acp":
        return OpenAIAnalyzerAdapter(
            api_key=resolved_settings.openai_api_key,
            model=resolved_settings.openai_model,
        )

    fallback_adapter = (
        OpenAIAnalyzerAdapter(
            api_key=resolved_settings.openai_api_key,
            model=resolved_settings.openai_model,
        )
        if resolved_settings.acp_fallback_openai and resolved_settings.openai_api_key.strip()
        else None
    )
    return ACPAnalyzerAdapter(
        base_url=resolved_settings.acp_base_url,
        api_key=resolved_settings.acp_api_key,
        model=resolved_settings.acp_model,
        timeout_seconds=resolved_settings.acp_timeout_seconds,
        fallback_adapter=fallback_adapter,
    )
