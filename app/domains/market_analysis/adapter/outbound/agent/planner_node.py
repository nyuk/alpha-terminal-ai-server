import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.agent_state import MultiAgentState

logger = logging.getLogger(__name__)

_SYSTEM = """당신은 AI_BRIEFING의 주식 시장 분석 플래너입니다.
사용자의 질문을 받아 어떤 측면을 분석해야 할지 계획을 세웁니다.

규칙:
- 매수, 매도, 보유, 관망, 비중 조절 추천도 분석 계획에 포함할 수 있습니다.
- 계획은 번호 목록으로 3개 이내로 작성합니다.
- 관련 종목명, 뉴스, 실적, 수급, 리스크, 밸류에이션, 시장 맥락을 구체적으로 지정합니다.
- 사용자가 추천을 요구하면 최종 답변에서 매수/매도/보유 판단을 할 수 있도록 근거와 확인 조건을 계획합니다.
"""


def planner_node(state: MultiAgentState) -> dict:
    """Planner node: 사용자 질문을 분석하고 분석 계획을 만든다."""
    query = state["query"]
    logger.info("[Planner] start query=%s", query[:80])

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=f"질문: {query}"),
    ]

    try:
        response = llm.invoke(messages)
        plan = response.content
        logger.info("[Planner] output plan=%s", plan[:120])
        return {
            "plan": plan,
            "messages": [*messages, response],
        }
    except Exception as e:
        logger.error("[Planner] failed: %s", e)
        raise RuntimeError(f"Planner node failed: {e}") from e
