import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.agent_state import MultiAgentState

logger = logging.getLogger(__name__)

_SYSTEM = """당신은 주식 분석 결과를 검토하는 리뷰어입니다.
Analyst가 작성한 분석 결과를 검토하고 품질을 평가합니다.

FAIL 조건 (아래 중 하나라도 해당하면 FAIL):
- "매수하세요", "매도하세요", "사세요", "파세요" 등 직접적인 투자 행동 권유
- "목표주가 OOO원", "OOO% 수익 예상" 등 구체적 수익 예측
- "강력 추천", "지금 당장 투자" 등 단정적 투자 권유

PASS 조건 (사실 기반 표현은 허용):
- 현재 주가, 52주 고점·저점, 시가총액 등 객관적 지표 언급
- "현재 보유 중", "관심종목으로 등록된" 등 상태 기술
- 재무 실적, 업종 동향, 리스크 요인 등 정보성 분석
- 분석 내용이 질문에 실질적으로 답하고 있음

답변 형식 (반드시 준수):
PASS: [한 줄 피드백]
또는
FAIL: [개선이 필요한 이유]"""


def reviewer_node(state: MultiAgentState) -> dict:
    """Reviewer 노드: Analyst 결과를 검토하고 품질 통과 여부를 판정한다."""
    query = state["query"]
    analysis = state.get("analysis", "")
    logger.info("[Reviewer] start analysis=%s", analysis[:80])

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    human_content = f"원본 질문: {query}\n\n분석 결과:\n{analysis}"
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human_content),
    ]

    try:
        response = llm.invoke(messages)
        verdict = response.content.strip()
        review_passed = verdict.upper().startswith("PASS")
        logger.info("[Reviewer] verdict=%s review_passed=%s", verdict[:80], review_passed)

        final_output = analysis if review_passed else None
        return {
            "review_passed": review_passed,
            "final_output": final_output,
            "messages": [*messages, response],
        }
    except Exception as e:
        logger.error("[Reviewer] failed: %s", e)
        raise RuntimeError(f"Reviewer 노드 실패: {e}") from e
