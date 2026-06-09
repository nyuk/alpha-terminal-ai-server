import json
from datetime import datetime
from typing import Any

from openai import AsyncOpenAI

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
  "summary": "한국어 사실 기반 요약문 (1~3문장, 빈 문자열 금지)",
  "tags": [
    {{"label": "태그명(한글)", "category": "CAPITAL|EARNINGS|PRODUCT|MANAGEMENT|INDUSTRY|RISK|OTHER"}}
  ],
  "sentiment": "POSITIVE|NEGATIVE|NEUTRAL",
  "sentiment_score": 0.0,
  "confidence": 0.8
}}

규칙:
- summary: 제공된 제목과 본문의 사실만 기반으로 1~3문장 작성. 본문이 짧더라도 제목에서 파악되는 핵심 사실을 포함할 것. 투자 판단에 중요한 리스크/호재를 명확히 쓸 것. 없는 내용을 지어내지 말 것. 반드시 한 글자 이상 작성
- tags: 핵심 태그 최대 5개. label은 한글 키워드
- tags[].category: CAPITAL(자본변동), EARNINGS(실적), PRODUCT(제품/서비스), MANAGEMENT(경영진), INDUSTRY(산업동향), RISK(리스크), OTHER(기타) 중 하나
- sentiment: POSITIVE(긍정) | NEGATIVE(부정) | NEUTRAL(중립) 중 하나
- sentiment_score: -1.0(완전부정) ~ 0.0(중립) ~ 1.0(완전긍정)
- confidence: 분석 가능한 정보량 기준. DART 공시·재무보고서: 0.90~0.98 / 뉴스 전문: 0.80~0.92 / 뉴스 요약(snippet): 0.65~0.80 / 제목만 50자 미만: 0.50~0.65"""

MULTI_ARTICLE_PROMPT_TEMPLATE = """다음은 {name}({symbol})에 대한 최근 뉴스 {count}건입니다. 이를 종합하여 투자 관련 핵심 내용을 분석해주세요.

{articles_text}

아래 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.

{{
  "summary": "한국어 종합 요약문 (2~4문장, 빈 문자열 금지)",
  "tags": [
    {{"label": "태그명(한글)", "category": "CAPITAL|EARNINGS|PRODUCT|MANAGEMENT|INDUSTRY|RISK|OTHER"}}
  ],
  "sentiment": "POSITIVE|NEGATIVE|NEUTRAL",
  "sentiment_score": 0.0,
  "confidence": 0.85
}}

규칙:
- summary: {count}건의 뉴스를 종합한 2~4문장 사실 기반 요약. 투자 판단에 중요한 리스크/호재를 명확히 쓸 것. 없는 내용을 지어내지 말 것. 반드시 한 글자 이상 작성
- tags: 핵심 태그 최대 5개. label은 한글 키워드
- tags[].category: CAPITAL(자본변동), EARNINGS(실적), PRODUCT(제품/서비스), MANAGEMENT(경영진), INDUSTRY(산업동향), RISK(리스크), OTHER(기타) 중 하나
- sentiment: 전체 뉴스를 종합한 시장 심리. POSITIVE|NEGATIVE|NEUTRAL
- sentiment_score: -1.0(완전부정) ~ 0.0(중립) ~ 1.0(완전긍정)
- confidence: 분석 가능한 정보량 기준 0.50~0.98"""


class OpenAIAnalyzerAdapter(ArticleAnalyzerPort):
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def analyze(self, article_id: str, title: str, body: str, category: str) -> AnalyzedArticle:
        prompt = PROMPT_TEMPLATE.format(
            category=category,
            title=title,
            body=body[:3000],
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        return _build_analyzed_article(
            article_id=article_id,
            data=data,
            default_confidence=0.5,
        )

    async def synthesize_articles(self, symbol: str, name: str, articles: list[dict]) -> AnalyzedArticle:
        articles_text_parts = []
        for i, art in enumerate(articles, 1):
            part = f"[기사 {i}] {art.get('published_at', '날짜 미상')}\n제목: {art.get('title', '')}\n내용: {art.get('body', '')[:800]}"
            articles_text_parts.append(part)
        articles_text = "\n\n".join(articles_text_parts)

        prompt = MULTI_ARTICLE_PROMPT_TEMPLATE.format(
            symbol=symbol,
            name=name,
            count=len(articles),
            articles_text=articles_text,
        )

        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)

        synthesis_id = f"synthesis_{symbol}_{int(datetime.now().timestamp())}"
        return _build_analyzed_article(
            article_id=synthesis_id,
            data=data,
            default_confidence=0.85,
        )


def _build_analyzed_article(
    article_id: str,
    data: dict[str, Any],
    default_confidence: float,
) -> AnalyzedArticle:
    summary = str(data.get("summary", "")).strip()
    if not summary:
        raise RuntimeError(
            "Analyzer response is missing a non-empty summary: "
            f"{json.dumps(data, ensure_ascii=False)[:700]}"
        )

    tags = []
    for tag in data.get("tags", []):
        if not isinstance(tag, dict):
            continue
        try:
            category = TagCategory(tag.get("category", "OTHER"))
        except ValueError:
            category = TagCategory.OTHER
        tags.append(TagItem(label=str(tag.get("label", "")), category=category))

    return AnalyzedArticle(
        article_id=article_id,
        summary=summary,
        tags=tags,
        sentiment=str(data.get("sentiment", "NEUTRAL")),
        sentiment_score=float(data.get("sentiment_score", 0.0)),
        confidence=float(data.get("confidence", default_confidence)),
        analyzer_version=ANALYZER_VERSION,
    )
