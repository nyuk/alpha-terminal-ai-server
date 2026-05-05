from app.domains.llm.application.usecase.text_generation_port import TextGenerationPort
from app.infrastructure.config.settings import get_settings
from app.infrastructure.llm.openai_responses_client import OpenAIResponsesTextClient


def get_text_generation_port() -> TextGenerationPort:
    settings = get_settings()
    return OpenAIResponsesTextClient(
        api_key=settings.openai_api_key,
        model=settings.openai_responses_model,
    )
