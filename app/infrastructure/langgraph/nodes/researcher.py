"""Researcher 노드 — 뉴스·시장 데이터 정보 수집."""
import logging

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "당신은 주식 시장 리서처입니다. "
    "플래너가 수립한 계획을 바탕으로 관심종목과 관련된 최신 동향, "
    "뉴스, 공시, 재무 지표 등 사실 기반 정보를 정리합니다. "
    "투자 추천·매수·매도 권유는 절대 하지 않습니다. "
    "수집된 정보를 항목별로 간결하게 정리하세요."
)


def researcher_node(state: AgentState) -> dict:
    logger.info("[Researcher] 시작 account_id=%s", state.get("account_id"))
    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.langgraph_model)

    messages = state.get("messages", [])
    plan = messages[-1].content if messages else ""
    context = state.get("watchlist_context") or "없음"

    prompt = (
        f"플래너 계획:\n{plan}\n\n"
        f"관심종목 컨텍스트: {context}\n\n"
        "위 계획에 따라 수집해야 할 정보를 정리해주세요."
    )

    try:
        response = llm.invoke([
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        research: str = response.content
        logger.info("[Researcher] 완료 research_length=%d", len(research))
        return {
            "messages": [AIMessage(content=research, name="researcher")],
            "current_node": "researcher",
        }
    except Exception as e:
        logger.exception("[Researcher] LLM 호출 실패")
        raise RuntimeError(f"Researcher 노드 실패: {e}") from e
