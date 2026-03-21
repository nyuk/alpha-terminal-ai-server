import json
from typing import Tuple

from openai import OpenAI

from app.domains.stock_analyzer.application.usecase.sentiment_analysis_port import SentimentAnalysisPort
from app.infrastructure.config.settings import get_settings

PROMPT_TEMPLATE = """다음 기사를 분석하여 아래 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.

제목: {title}
본문: {body}

응답 형식:
{{
  "sentiment": "POSITIVE|NEGATIVE|NEUTRAL",
  "sentiment_score": 0.0
}}

규칙:
- sentiment: POSITIVE(긍정) | NEGATIVE(부정) | NEUTRAL(중립) 중 하나
- sentiment_score: -1.0(완전부정) ~ 0.0(중립) ~ 1.0(완전긍정)
- 투자 추천/비추천 판단 금지, 사실 기반 감정만 분석"""


class OpenAISentimentAdapter(SentimentAnalysisPort):
    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)

    async def analyze(self, title: str, body: str) -> Tuple[str, float]:
        prompt = PROMPT_TEMPLATE.format(title=title, body=body[:3000])

        response = self._client.chat.completions.create(
            model=get_settings().openai_model,
            messages=[{"role": "user", "content": prompt}],
        )

        data = json.loads(response.choices[0].message.content.strip())
        return data.get("sentiment", "NEUTRAL"), float(data.get("sentiment_score", 0.0))
