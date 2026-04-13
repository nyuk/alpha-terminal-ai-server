"""Planner 노드 — 관심종목 분석 계획 수립."""
import logging

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "당신은 주식 시장 분석 플래너입니다. "
    "사용자의 관심종목과 분석 요청을 바탕으로 조사 계획을 수립합니다. "
    "투자 추천·매수·매도 권유는 절대 하지 않습니다. "
    "어떤 정보를 수집하고 분석할지 간결하게 3단계 계획으로 작성하세요."
)


def planner_node(state: AgentState) -> dict:
    logger.info("[Planner] 시작 account_id=%s task=%.80s", state.get("account_id"), state.get("task"))
    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.langgraph_model)

    context = state.get("watchlist_context") or "없음"
    prompt = f"분석 요청: {state.get('task', '')}\n관심종목 컨텍스트: {context}"

    try:
        response = llm.invoke([
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        plan: str = response.content
        logger.info("[Planner] 완료 plan_length=%d", len(plan))
        return {
            "messages": [AIMessage(content=plan, name="planner")],
            "current_node": "planner",
        }
    except Exception as e:
        logger.exception("[Planner] LLM 호출 실패")
        raise RuntimeError(f"Planner 노드 실패: {e}") from e
