"""Query Parser — 자연어 투자 질문을 구조화된 쿼리 데이터로 변환한다.

출력 구조:
    company       : 종목명 또는 티커 (식별 불가 시 None)
    intent        : 사용자 의도 (매수 판단 / 리스크 분석 / 전망 조회 / 섹터 분석 등)
    required_data : 후속 에이전트가 수집해야 할 데이터 유형 목록 (SOURCE_REGISTRY 키)
"""
import json
import re
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict

from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

MAX_RETRIES = 2

# ---------------------------------------------------------------------------
# SOURCE_REGISTRY: 실제 구현된 데이터 소스 목록
# Key   → Query Parser가 required_data에 사용하는 식별자
# Value → 설명 (프롬프트·로그용)
# ---------------------------------------------------------------------------
SOURCE_REGISTRY: dict[str, str] = {
    "뉴스": "SERP API 구글 뉴스 검색 — 최신 기사·공시·시황",
    "YouTube 영상": "YouTube Data API 채널 영상 검색 — 증권 채널 영상 및 댓글",
    "종목": "관심종목 기본 정보 — 시세·재무 요약 (향후 구현)",
}

# fallback: 파싱 실패 또는 유효 키가 없을 때 기본 수집 소스 (전체 소스)
DEFAULT_SOURCES: List[str] = ["뉴스", "YouTube 영상", "종목"]

_VALID_KEYS = set(SOURCE_REGISTRY.keys())


class ParsedQuery(TypedDict):
    """구조화된 투자 질의 파싱 결과."""

    company: Optional[str]
    intent: str
    required_data: List[str]      # SOURCE_REGISTRY 키만 포함


class QueryParseError(Exception):
    """Query Parser 실패 예외 — 형식 오류 또는 의미 없는 입력."""


_SOURCE_DESC = "\n".join(
    f'   - "{k}": {v}' for k, v in SOURCE_REGISTRY.items()
)

_SYSTEM = f"""당신은 투자 질문 분석기입니다.
사용자의 자연어 투자 질문에서 다음 세 가지를 추출하여 반드시 JSON 형식으로만 응답하세요.

추출 항목:
1. company       : 질문에 언급된 종목명 또는 티커 심볼. 특정 종목이 없으면 null.
                   예: "한화에어로스페이스", "삼성전자", "TSMC", null
2. intent        : 사용자의 투자 의도를 한 문장으로 요약.
                   예: "매수 타이밍 판단", "리스크 분석", "전망 조회", "섹터 전반 분석"
3. required_data : 질문에 답하기 위해 필요한 데이터 유형 목록 (배열).
                   반드시 아래 목록에서만 선택하세요 (여러 개 선택 가능):
{_SOURCE_DESC}

   선택 기준:
   - 최신 뉴스·공시·시황이 필요하면 → "뉴스" 포함
   - 유튜브 증권 채널 해설·전문가 의견이 필요하면 → "YouTube 영상" 포함
   - 종목 시세·재무 정보가 필요하면 → "종목" 포함
   - 불확실하면 세 가지 모두 포함

응답 형식 (JSON만, 다른 텍스트 없이):
{{
  "company": "한화에어로스페이스",
  "intent": "매수 타이밍 판단",
  "required_data": ["뉴스", "YouTube 영상", "종목"]
}}

예시:
- "한화에어로스페이스 지금 사도 될까?" →
  {{"company": "한화에어로스페이스", "intent": "매수 타이밍 판단", "required_data": ["뉴스", "YouTube 영상", "종목"]}}
- "방산주 전반 뉴스 알려줘" →
  {{"company": null, "intent": "섹터 뉴스 조회", "required_data": ["뉴스"]}}
- "삼성전자 유튜브 반응은?" →
  {{"company": "삼성전자", "intent": "유튜브 여론 조회", "required_data": ["YouTube 영상"]}}
- "삼성전자 리스크 분석해줘" →
  {{"company": "삼성전자", "intent": "리스크 분석", "required_data": ["뉴스", "YouTube 영상", "종목"]}}
- "방산주 전반 전망 알려줘" →
  {{"company": null, "intent": "섹터 전반 분석", "required_data": ["뉴스", "YouTube 영상", "종목"]}}

주의:
- JSON 외 다른 텍스트를 포함하지 마세요.
- company 가 없는 경우 반드시 null 로 표기하세요.
- required_data 는 위 목록의 키만 사용하세요.
- required_data 는 최소 1개 이상이어야 합니다."""


def _extract_json(text: str) -> dict:
    """LLM 응답에서 JSON 블록을 추출한다."""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        return json.loads(match.group(1))
    match = re.search(r"\{[\s\S]+\}", text)
    if match:
        return json.loads(match.group(0))
    raise QueryParseError(f"JSON 블록을 찾을 수 없습니다: {text[:200]}")


def _validate_and_filter(data: dict) -> ParsedQuery:
    """파싱 결과를 SOURCE_REGISTRY 키로 필터링하고 fallback을 적용한다."""
    if "intent" not in data or not data.get("intent"):
        raise QueryParseError(f"intent 필드가 없거나 비어있습니다: {data}")

    raw_required = data.get("required_data", [])
    if not isinstance(raw_required, list):
        raw_required = []

    # SOURCE_REGISTRY 등록 키만 통과
    valid = [item for item in raw_required if item in _VALID_KEYS]

    if not valid:
        valid = list(DEFAULT_SOURCES)

    return ParsedQuery(
        company=data.get("company") or None,
        intent=str(data["intent"]),
        required_data=valid,
    )


async def parse_investment_query(query: str) -> ParsedQuery:
    """자연어 투자 질문을 ParsedQuery 구조체로 변환한다.

    Args:
        query: 사용자의 자연어 투자 질문 (예: "한화에어로스페이스 지금 사도 될까?")

    Returns:
        ParsedQuery: company / intent / required_data 구조체

    Raises:
        QueryParseError: LLM 응답 형식 오류 또는 의미 없는 입력
    """
    await aemit(f"[QueryParser] ▶ start | query={query[:80]}")
    await aemit(f"[QueryParser]   SOURCE_REGISTRY={list(SOURCE_REGISTRY.keys())}")

    if not query or not query.strip():
        raise QueryParseError("질문이 비어있습니다.")

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=f"투자 질문: {query}"),
    ]

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = await llm.ainvoke(messages)
            raw = response.content.strip()
            await aemit(f"[QueryParser]   attempt={attempt} raw={raw[:150]}")

            data = _extract_json(raw)
            result = _validate_and_filter(data)

            await aemit(f"[QueryParser] ◀ company={result['company']} | intent={result['intent']}")
            await aemit(f"[QueryParser]   required_data={result['required_data']}")

            return result

        except (json.JSONDecodeError, QueryParseError) as e:
            await aemit(f"[QueryParser] ⚠ attempt={attempt} parse error: {e}")
            last_error = e
            messages = [
                SystemMessage(content=_SYSTEM),
                HumanMessage(content=f"투자 질문: {query}"),
                HumanMessage(
                    content=f"이전 응답이 올바른 JSON 형식이 아니었습니다. 반드시 JSON만 응답하세요. 오류: {e}"
                ),
            ]

    raise QueryParseError(f"Query 파싱 {MAX_RETRIES}회 실패: {last_error}") from last_error
