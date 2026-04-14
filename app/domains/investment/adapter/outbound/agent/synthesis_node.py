from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.domains.investment.adapter.outbound.agent.investment_agent_state import InvestmentAgentState
from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

_DISCLAIMER = (
    "\n\n※ 면책 문구: 본 응답은 투자 권유가 아닌 정보 제공을 목적으로 합니다. "
    "투자 결정은 본인의 판단과 책임 하에 이루어져야 하며, "
    "본 정보는 투자 결과를 보장하지 않습니다."
)

_SYSTEM = """당신은 투자 정보 종합 에이전트입니다.
Analysis Agent가 생성한 인사이트를 바탕으로 사용자의 투자 질문에 대한 종합적인 참고 응답을 작성합니다.

응답 작성 원칙:
- 분석 결과를 사용자가 이해하기 쉬운 언어로 요약합니다.
- 종목 전망, 리스크, 투자 포인트를 균형 있게 제시합니다.
- 투자 추천(매수/매도)은 절대 포함하지 않습니다.
- 한국어로 자연스럽게 작성합니다.
- 응답 말미에 면책 문구가 자동으로 추가됩니다."""


async def synthesis_node(state: InvestmentAgentState) -> dict:
    """Synthesis 노드: 분석 결과를 기반으로 최종 사용자 응답을 생성한다.

    투자 권유가 아닌 정보 제공임을 명시하는 면책 문구를 포함한다.
    """
    query = state["query"]
    analysis = state.get("analysis", "")

    await aemit(f"[Synthesis] ▶ 시작 | 분석 결과 종합 중...")

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    human_content = (
        f"사용자 질문: {query}\n\n"
        f"분석 결과:\n{analysis}\n\n"
        "위 분석을 바탕으로 사용자에게 제공할 투자 판단 참고 응답을 작성하세요."
    )
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human_content),
    ]

    response = await llm.ainvoke(messages)
    final_answer = response.content + _DISCLAIMER

    await aemit(f"[Synthesis] ◀ 최종 응답 생성 완료 | {len(final_answer)}자")

    return {
        "final_answer": final_answer,
        "messages": [*messages, response],
    }
