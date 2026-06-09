import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.infrastructure.config.settings import get_settings
from app.infrastructure.langgraph.agent_state import MultiAgentState

logger = logging.getLogger(__name__)

_SYSTEM = """당신은 AI_BRIEFING의 주식 시장 분석가입니다.
Planner가 만든 계획을 바탕으로 사용자의 질문에 답합니다.

규칙:
- 매수, 매도, 보유, 관망, 비중 축소/확대 추천까지 다룰 수 있습니다.
- 사용자가 추천을 요구하면 결론을 피하지 말고, 근거와 반대 시나리오를 함께 둡니다.
- 불확실한 내용은 불확실하다고 밝히고, 없는 사실을 만들지 않습니다.
- 리스크 요인이 있으면 반드시 언급합니다.
- 답변은 한국어로 간결하게 작성합니다.
"""


def analyst_node(state: MultiAgentState) -> dict:
    """Analyst node: Planner 계획을 바탕으로 실제 분석을 수행한다."""
    query = state["query"]
    plan = state.get("plan", "")
    retry_count = state.get("retry_count", 0)
    logger.info("[Analyst] start query=%s retry=%s", query[:80], retry_count)

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    human_content = f"질문: {query}\n\n분석 계획:\n{plan}"
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human_content),
    ]

    try:
        response = llm.invoke(messages)
        analysis = response.content
        logger.info("[Analyst] output analysis=%s", analysis[:120])
        return {
            "analysis": analysis,
            "retry_count": retry_count + 1,
            "messages": [*messages, response],
        }
    except Exception as e:
        logger.error("[Analyst] failed: %s", e)
        raise RuntimeError(f"Analyst node failed: {e}") from e
