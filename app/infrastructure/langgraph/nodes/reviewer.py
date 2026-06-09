"""Reviewer 노드 — 최종 AI_BRIEFING 결과 검토."""
import logging

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "당신은 AI_BRIEFING 결과를 검토하는 리뷰어입니다. "
    "애널리스트 분석 결과가 사용자 질문과 관심종목 범위에 맞는지 확인합니다. "
    "매수, 매도, 보유, 관망 추천은 조건과 근거, 리스크가 함께 있으면 유지합니다. "
    "근거 없는 목표가, 보장 수익률, 확정적 미래 예측은 제거하거나 근거 기반 표현으로 고칩니다. "
    "최종 출력은 결론, 판단 근거, 리스크, 매수/매도/보유 추천, 확인할 데이터 순서로 명확하게 작성하세요."
)


def reviewer_node(state: AgentState) -> dict:
    logger.info("[Reviewer] 시작 account_id=%s", state.get("account_id"))
    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.langgraph_model)

    messages = state.get("messages", [])
    analysis = messages[-1].content if messages else ""

    prompt = (
        f"애널리스트 분석 결과:\n{analysis}\n\n"
        "위 내용을 검토하여 AI_BRIEFING 최종 출력을 작성해주세요."
    )

    try:
        response = llm.invoke([
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        final: str = response.content
        logger.info("[Reviewer] 완료 final_length=%d", len(final))
        return {
            "messages": [AIMessage(content=final, name="reviewer")],
            "current_node": "reviewer",
            "final_output": final,
        }
    except Exception as e:
        logger.exception("[Reviewer] LLM 호출 실패")
        raise RuntimeError(f"Reviewer 노드 실패: {e}") from e
