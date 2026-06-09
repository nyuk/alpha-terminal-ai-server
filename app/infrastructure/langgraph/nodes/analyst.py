"""Analyst 노드 — 수집된 정보 분석·요약."""
import logging

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "당신은 AI_BRIEFING의 주식 시장 애널리스트입니다. "
    "리서처가 수집한 정보를 바탕으로 관심종목별 핵심 요약, 리스크 요인, 투자 판단 관점을 도출합니다. "
    "매수, 매도, 보유, 관망, 비중 축소/확대 추천까지 다룰 수 있습니다. "
    "사용자가 추천을 요구하면 결론을 피하지 말고 현재 관점의 판단을 제시합니다. "
    "다만 목표가, 수익률, 확정적 미래를 지어내지 말고 조건과 근거를 함께 제시하세요. "
    "종목별로 3~5줄 요약, 리스크 태그, 매수/매도/보유 추천을 작성하세요."
)


def analyst_node(state: AgentState) -> dict:
    logger.info("[Analyst] 시작 account_id=%s", state.get("account_id"))
    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.langgraph_model)

    messages = state.get("messages", [])
    research = messages[-1].content if messages else ""

    prompt = (
        f"리서처 수집 정보:\n{research}\n\n"
        "위 정보를 분석하여 종목별 요약, 리스크 태그, 매수/매도/보유 추천을 작성해주세요."
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
