import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.agent_state import MultiAgentState

logger = logging.getLogger(__name__)

_SYSTEM = """당신은 AI_BRIEFING 결과를 검토하는 리뷰어입니다.
Analyst가 작성한 분석 결과를 검토하고 최종 통과 여부를 판단합니다.

FAIL 조건:
- 근거 없이 확정 수익률이나 목표가를 만들어냄
- "반드시 오른다", "절대 손실 없다"처럼 근거 없이 확정적으로 말함
- 질문과 무관한 종목 또는 관심종목 범위 밖의 내용을 핵심 결론으로 삼음

PASS 조건:
- 매수, 매도, 보유, 관망 추천이 조건과 근거를 함께 제시함
- 리스크와 반대 시나리오를 함께 제시함
- 사용자의 질문에 직접 답함

응답 형식:
PASS: [한 줄 피드백]
또는
FAIL: [개선이 필요한 이유]
"""


def reviewer_node(state: MultiAgentState) -> dict:
    """Reviewer node: Analyst 결과를 검토하고 최종 통과 여부를 판정한다."""
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
        raise RuntimeError(f"Reviewer node failed: {e}") from e
