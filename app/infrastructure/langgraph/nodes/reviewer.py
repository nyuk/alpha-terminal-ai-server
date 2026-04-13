"""Reviewer 노드 — 최종 결과 검토 및 투자 추천 필터링."""
import logging

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "당신은 준법 감시 리뷰어입니다. "
    "애널리스트 분석 결과를 검토하여 투자 추천·매수·매도 권유 표현이 포함되어 있으면 제거하고, "
    "사실 기반 정보 요약만 남깁니다. "
    "최종 출력은 사용자에게 직접 전달될 내용이므로 명확하고 간결하게 작성하세요."
)


def reviewer_node(state: AgentState) -> dict:
    logger.info("[Reviewer] 시작 account_id=%s", state.get("account_id"))
    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.langgraph_model)

    messages = state.get("messages", [])
    analysis = messages[-1].content if messages else ""

    prompt = (
        f"애널리스트 분석 결과:\n{analysis}\n\n"
        "위 내용을 검토하여 투자 추천 표현을 제거하고 최종 출력을 작성해주세요."
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
