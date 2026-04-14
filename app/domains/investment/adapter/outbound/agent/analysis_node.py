from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.domains.investment.adapter.outbound.agent.investment_agent_state import InvestmentAgentState
from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

_SYSTEM = """당신은 투자 분석 전문 에이전트입니다.
Retrieval Agent가 수집한 원천 데이터를 기반으로 다음 항목을 분석합니다:

1. 종목 전망: 현재 상황과 향후 전망에 대한 객관적 분석
2. 리스크 요인: 투자 시 고려해야 할 위험 요소
3. 투자 포인트: 주목해야 할 주요 요인

규칙:
- 투자 추천(매수/매도) 의견은 절대 제공하지 않습니다.
- 수집된 데이터에 근거하여 분석합니다.
- 불확실한 내용은 명시합니다.
- 분석 결과는 구조화하여 작성합니다."""


async def analysis_node(state: InvestmentAgentState) -> dict:
    """Analysis 노드: 수집된 데이터를 기반으로 종목 전망·리스크·투자 포인트를 분석한다."""
    query = state["query"]
    retrieved_data = state.get("retrieved_data", "")

    await aemit(f"[Analysis] ▶ 시작 | query={query[:60]}")
    await aemit(f"[Analysis]   수집 데이터 {len(retrieved_data)}자 분석 중...")

    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    human_content = (
        f"투자 질문: {query}\n\n"
        f"수집된 원천 데이터:\n{retrieved_data}\n\n"
        "위 정보를 바탕으로 종목 전망, 리스크, 투자 포인트를 분석하세요."
    )
    messages = [
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=human_content),
    ]

    response = await llm.ainvoke(messages)
    analysis = response.content

    await aemit(f"[Analysis] ◀ 분석 완료 | {len(analysis)}자 생성")

    return {
        "analysis": analysis,
        "messages": [*messages, response],
    }
