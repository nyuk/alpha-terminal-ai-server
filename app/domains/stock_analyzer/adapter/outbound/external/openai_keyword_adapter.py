import json
from typing import List

from openai import OpenAI

from app.domains.stock_analyzer.application.usecase.keyword_extraction_port import KeywordExtractionPort

PROMPT_TEMPLATE = """다음 기사를 분석하여 아래 JSON 형식으로만 응답해주세요. 다른 텍스트는 포함하지 마세요.

제목: {title}
본문: {body}

응답 형식:
{{
  "keywords": ["키워드1", "키워드2", "키워드3", "키워드4", "키워드5"]
}}

규칙:
- keywords: 핵심 키워드 최대 5개, 한글 키워드"""


class OpenAIKeywordAdapter(KeywordExtractionPort):
    def __init__(self, api_key: str):
        self._client = OpenAI(api_key=api_key)

    async def extract(self, title: str, body: str) -> List[str]:
        prompt = PROMPT_TEMPLATE.format(title=title, body=body[:3000])

        response = self._client.responses.create(
            model="gpt-5-mini",
            input=prompt,
        )

        data = json.loads(response.output_text.strip())
        return data.get("keywords", [])
