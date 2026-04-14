from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.domains.investment.adapter.outbound.agent.investment_agent_state import (
    InvestmentAgentState,
    NEXT_RETRIEVAL,
    NEXT_ANALYSIS,
    NEXT_SYNTHESIS,
    NEXT_END,
)
from app.domains.investment.adapter.outbound.agent.query_parser import (
    parse_investment_query,
    QueryParseError,
)
from app.domains.investment.adapter.outbound.agent.log_context import aemit
from app.infrastructure.config.settings import get_settings

MAX_ITERATIONS = 6

_SYSTEM = """당신은 투자 판단 멀티 에이전트 워크플로우의 Orchestrator입니다.
현재 상태를 파악하고 다음에 실행해야 할 에이전트를 결정합니다.

현재 상태 정보:
- parsed_query: {parsed_query}
- retrieved_data: {retrieved_data}
- analysis: {analysis}

선택 규칙:
1. retrieved_data가 없으면 → RETRIEVAL
2. retrieved_data는 있으나 analysis가 없으면 → ANALYSIS
3. retrieved_data와 analysis가 모두 있으면 → SYNTHESIS
4. 응답이 이미 완성되었거나 반복 한계에 도달했으면 → END

반드시 다음 중 하나의 키워드만 단독으로 출력하세요:
RETRIEVAL
ANALYSIS
SYNTHESIS
END"""


async def orchestrator_node(state: InvestmentAgentState) -> dict:
    """Orchestrator 노드: Query Parser 호출 후 다음 실행 에이전트를 결정한다.

    최초 실행(iteration_count=0)에서 Query Parser를 호출하여
    구조화된 쿼리를 State에 기록한다.
    """
    query = state["query"]
    iteration_count = state.get("iteration_count", 0)
    parsed_query = state.get("parsed_query")
    retrieved_data = state.get("retrieved_data")
    analysis = state.get("analysis")

    await aemit(f"[Orchestrator] ▶ iteration {iteration_count + 1} 시작")
    await aemit(f"[Orchestrator]   retrieved={'있음' if retrieved_data else '없음'} | analysis={'있음' if analysis else '없음'}")

    # --- Query Parser: 최초 실행 시에만 호출 ---
    updates: dict = {}
    if iteration_count == 0 and parsed_query is None:
        await aemit(f"[Orchestrator]   → Query Parser 호출")
        try:
            parsed_query = await parse_investment_query(query)
            updates["parsed_query"] = dict(parsed_query)
            await aemit(f"[Orchestrator]   parsed_query 완료: company={parsed_query['company']}, intent={parsed_query['intent']}")
        except QueryParseError as e:
            await aemit(f"[Orchestrator] ✗ Query Parser 실패: {e}")
            raise

    # --- 반복 한계 초과 ---
    if iteration_count >= MAX_ITERATIONS:
        await aemit(f"[Orchestrator] ⚠ max iterations({MAX_ITERATIONS}) reached → END")
        return {**updates, "next_agent": NEXT_END, "iteration_count": iteration_count + 1}

    # --- LLM 라우팅 결정 ---
    settings = get_settings()
    llm = ChatOpenAI(api_key=settings.openai_api_key, model=settings.openai_model)

    system_content = _SYSTEM.format(
        parsed_query=parsed_query or "파싱 전",
        retrieved_data="수집됨" if retrieved_data else "없음",
        analysis="생성됨" if analysis else "없음",
    )
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=f"사용자 질문: {query}"),
    ]

    response = await llm.ainvoke(messages)
    decision = response.content.strip().upper()

    next_agent_map = {
        "RETRIEVAL": NEXT_RETRIEVAL,
        "ANALYSIS": NEXT_ANALYSIS,
        "SYNTHESIS": NEXT_SYNTHESIS,
        "END": NEXT_END,
    }
    next_agent = next_agent_map.get(decision, NEXT_END)

    await aemit(f"[Orchestrator] ◀ 다음 에이전트: {decision}")

    return {
        **updates,
        "next_agent": next_agent,
        "iteration_count": iteration_count + 1,
        "messages": [*messages, response],
    }
