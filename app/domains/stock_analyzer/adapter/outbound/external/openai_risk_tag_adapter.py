import json
from typing import List

from openai import OpenAI

from app.domains.stock_analyzer.application.usecase.risk_tagging_port import RiskTaggingPort
from app.domains.stock_analyzer.domain.entity.tag_item import TagCategory, TagItem
from app.infrastructure.config.settings import get_settings

PROMPT_TEMPLATE = """다음 기사를 분석하여 아래 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.

제목: {title}
본문: {body}

응답 형식:
{{
  "risk_tags": [
    {{"label": "태그명(한글)", "category": "RISK"}}
  ]
}}

규칙:
- risk_tags: 리스크 관련 태그만 추출 (소송, 규제, 사고, 부채, 손실, 제재, 벌금 등)
- 리스크가 없으면 빈 배열 반환
- label은 한글 키워드, category는 반드시 RISK
- 투자 추천/비추천 표현 절대 금지, 사실 기반으로만 태깅"""


class OpenAIRiskTagAdapter(RiskTaggingPort):
    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)

    async def tag(self, title: str, body: str) -> List[TagItem]:
        prompt = PROMPT_TEMPLATE.format(title=title, body=body[:3000])

        response = self._client.chat.completions.create(
            model=get_settings().openai_model,
            messages=[{"role": "user", "content": prompt}],
        )

        data = json.loads(response.choices[0].message.content.strip())
        return [
            TagItem(label=t.get("label", ""), category=TagCategory.RISK)
            for t in data.get("risk_tags", [])
        ]
