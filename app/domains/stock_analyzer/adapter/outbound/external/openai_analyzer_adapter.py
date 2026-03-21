import json

from openai import OpenAI

from app.domains.stock_analyzer.application.usecase.article_analyzer_port import ArticleAnalyzerPort
from app.domains.stock_analyzer.domain.entity.analyzed_article import AnalyzedArticle
from app.domains.stock_analyzer.domain.entity.tag_item import TagCategory, TagItem

ANALYZER_VERSION = "analyzer-v1.0.0"

PROMPT_TEMPLATE = """다음 기사를 분석하여 아래 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.

카테고리: {category}
제목: {title}
본문: {body}

응답 형식:
{{
  "summary": "사실 기반 요약문 (1~3문장, 투자 추천/비추천 표현 절대 금지)",
  "tags": [
    {{"label": "태그명(한글)", "category": "CAPITAL|EARNINGS|PRODUCT|MANAGEMENT|INDUSTRY|RISK|OTHER"}}
  ],
  "sentiment": "POSITIVE|NEGATIVE|NEUTRAL",
  "sentiment_score": -1.0,
  "confidence": 0.95
}}

규칙:
- summary: 사실만 기반으로 1~3문장 이내 작성. 투자 추천/비추천 표현 절대 금지
- tags: 핵심 태그 최대 5개. label은 한글 키워드
- tags[].category: CAPITAL(자본변동), EARNINGS(실적), PRODUCT(제품/서비스), MANAGEMENT(경영진), INDUSTRY(산업동향), RISK(리스크), OTHER(기타) 중 하나
- sentiment: POSITIVE(긍정) | NEGATIVE(부정) | NEUTRAL(중립) 중 하나
- sentiment_score: -1.0(완전부정) ~ 0.0(중립) ~ 1.0(완전긍정)
- confidence: 0.0 ~ 1.0 (DART 공시: 0.90~0.98, 뉴스: 0.80~0.92, 짧은본문<50자: 0.50~0.75)"""


class OpenAIAnalyzerAdapter(ArticleAnalyzerPort):
    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)

    async def analyze(self, article_id: str, title: str, body: str, category: str) -> AnalyzedArticle:
        prompt = PROMPT_TEMPLATE.format(
            category=category,
            title=title,
            body=body[:3000],
        )

        response = self._client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        tags = [
            TagItem(
                label=t.get("label", ""),
                category=TagCategory(t.get("category", "OTHER")),
            )
            for t in data.get("tags", [])
        ]

        return AnalyzedArticle(
            article_id=article_id,
            summary=data.get("summary", ""),
            tags=tags,
            sentiment=data.get("sentiment", "NEUTRAL"),
            sentiment_score=float(data.get("sentiment_score", 0.0)),
            confidence=float(data.get("confidence", 0.5)),
            analyzer_version=ANALYZER_VERSION,
        )
