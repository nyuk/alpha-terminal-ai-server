import json

from openai import OpenAI

from app.domains.news_analyzer.application.usecase.article_analysis_port import ArticleAnalysisPort
from app.domains.news_analyzer.domain.entity.analysis_result import AnalysisResult
from app.domains.news_analyzer.domain.value_object.sentiment import Sentiment
from app.infrastructure.config.settings import get_settings

SYSTEM_PROMPT = """당신은 뉴스 기사 분석 전문가입니다.
사용자가 제공하는 기사 본문을 분석하여 핵심 키워드와 감정 분석 결과를 반환하세요.

규칙:
1. keywords: 기사의 핵심 키워드 3~7개 (리스트)
2. sentiment: 감정 분석 결과 ("POSITIVE", "NEGATIVE", "NEUTRAL" 중 하나)
3. sentiment_score: 감정 점수 (-1.0 ~ 1.0, 부정일수록 -1에 가깝고 긍정일수록 1에 가까움)

반드시 아래 json 형식으로만 응답하세요:
{"keywords": ["키워드1", "키워드2"], "sentiment": "NEUTRAL", "sentiment_score": 0.0}

투자 추천이나 비추천은 절대 하지 마세요. 사실 기반 분석만 수행하세요."""

INPUT_TEMPLATE = "다음 기사 본문을 분석하여 json 형식으로 키워드와 감정 분석 결과를 반환하세요.\n\n{content}"


class OpenAIAnalysisAdapter(ArticleAnalysisPort):
    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)

    def analyze(self, content: str) -> AnalysisResult:
        response = self._client.chat.completions.create(
            model=get_settings().openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": INPUT_TEMPLATE.format(content=content[:3000])},
            ],
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)

        sentiment = Sentiment(data["sentiment"])
        score = max(-1.0, min(1.0, float(data["sentiment_score"])))

        return AnalysisResult(
            keywords=data["keywords"],
            sentiment=sentiment,
            sentiment_score=score,
        )
