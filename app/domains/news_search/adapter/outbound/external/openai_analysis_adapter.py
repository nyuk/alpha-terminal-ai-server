import json

from openai import OpenAI

from app.domains.news_search.application.usecase.article_analysis_port import ArticleAnalysisPort
from app.domains.news_search.domain.entity.article_analysis import ArticleAnalysis
from app.infrastructure.config.settings import get_settings

PROMPT_TEMPLATE = """다음 기사 본문을 분석하여 아래 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.

기사 본문:
{content}

응답 형식:
{{
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"],
  "sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
  "sentiment_score": -1.0 ~ 1.0
}}

- keywords: 핵심 키워드 최대 5개
- sentiment: POSITIVE(긍정), NEGATIVE(부정), NEUTRAL(중립) 중 하나
- sentiment_score: -1.0(완전 부정) ~ 0.0(중립) ~ 1.0(완전 긍정)"""


class OpenAIAnalysisAdapter(ArticleAnalysisPort):
    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)

    async def analyze(self, article_id: int, content: str) -> ArticleAnalysis:
        response = self._client.chat.completions.create(
            model=get_settings().openai_model,
            messages=[{"role": "user", "content": PROMPT_TEMPLATE.format(content=content[:3000])}],
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        return ArticleAnalysis(
            article_id=article_id,
            keywords=data.get("keywords", []),
            sentiment=data.get("sentiment", "NEUTRAL"),
            sentiment_score=float(data.get("sentiment_score", 0.0)),
        )
