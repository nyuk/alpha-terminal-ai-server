"""Analyst 노드 — 수집된 정보 분석·요약."""
import logging

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "당신은 주식 시장 애널리스트입니다. "
    "리서처가 수집한 정보를 바탕으로 관심종목별 핵심 요약과 리스크 요인을 도출합니다. "
    "투자 추천·매수·매도 권유는 절대 하지 않습니다. "
    "종목별로 3~5줄 요약과 리스크 태그를 작성하세요."
)


def analyst_node(state: AgentState) -> dict:
    logger.info("[Analyst] 시작 account_id=%s", state.get("account_id"))
    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.langgraph_model)

    messages = state.get("messages", [])
    research = messages[-1].content if messages else ""

    prompt = (
        f"리서처 수집 정보:\n{research}\n\n"
        "위 정보를 분석하여 종목별 요약과 리스크 태그를 작성해주세요."
    )

    try:
        response = llm.invoke([
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ])
        analysis: str = response.content
        logger.info("[Analyst] 완료 analysis_length=%d", len(analysis))
        return {
            "messages": [AIMessage(content=analysis, name="analyst")],
            "current_node": "analyst",
        }
    except Exception as e:
        logger.exception("[Analyst] LLM 호출 실패")
        return {
            "current_node": "analyst",
            "error": f"Analyst 노드 실패: {e}",
        }
