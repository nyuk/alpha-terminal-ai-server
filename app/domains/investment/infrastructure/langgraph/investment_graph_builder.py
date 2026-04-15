import logging

from langgraph.graph import END, START, StateGraph

from app.domains.investment.adapter.outbound.agent.investment_agent_state import (
    InvestmentAgentState,
    NEXT_RETRIEVAL,
    NEXT_ANALYSIS,
    NEXT_SYNTHESIS,
    NEXT_END,
)
from app.domains.investment.adapter.outbound.agent.orchestrator_node import orchestrator_node
from app.domains.investment.adapter.outbound.agent.retrieval_node import retrieval_node
from app.domains.investment.adapter.outbound.agent.analysis_node import analysis_node
from app.domains.investment.adapter.outbound.agent.synthesis_node import synthesis_node
from app.domains.investment.adapter.outbound.agent.log_context import aemit

logger = logging.getLogger(__name__)


def _route_from_orchestrator(state: InvestmentAgentState) -> str:
    """Orchestrator 결정에 따라 다음 노드를 선택한다.

    next_agent 값 → 노드 키 매핑:
      retrieval → Retrieval Agent
      analysis  → Analysis Agent
      synthesis → Synthesis Agent
      end       → END
    """
    next_agent = state.get("next_agent", NEXT_END)
    print(f"[Graph] routing from orchestrator → {next_agent}")
    return next_agent


def build_investment_graph():
    """투자 판단 멀티 에이전트 그래프를 빌드한다.

    흐름:
        START
          ↓
        Orchestrator  ─── 조건부 라우팅 ───→  Retrieval → Orchestrator
                                           →  Analysis  → Orchestrator
                                           →  Synthesis → END
                                           →  END
    """
    builder = StateGraph(InvestmentAgentState)

    # 노드 등록
    builder.add_node("orchestrator", orchestrator_node)
    builder.add_node(NEXT_RETRIEVAL, retrieval_node)
    builder.add_node(NEXT_ANALYSIS, analysis_node)
    builder.add_node(NEXT_SYNTHESIS, synthesis_node)

    # 진입점: START → Orchestrator
    builder.add_edge(START, "orchestrator")

    # Orchestrator 조건부 라우팅
    builder.add_conditional_edges(
        "orchestrator",
        _route_from_orchestrator,
        {
            NEXT_RETRIEVAL: NEXT_RETRIEVAL,
            NEXT_ANALYSIS: NEXT_ANALYSIS,
            NEXT_SYNTHESIS: NEXT_SYNTHESIS,
            NEXT_END: END,
        },
    )

    # 각 Agent 완료 후 Orchestrator로 복귀 (Synthesis는 종료)
    builder.add_edge(NEXT_RETRIEVAL, "orchestrator")
    builder.add_edge(NEXT_ANALYSIS, "orchestrator")
    builder.add_edge(NEXT_SYNTHESIS, END)

    return builder.compile()


_investment_graph = None


def get_investment_graph():
    global _investment_graph
    if _investment_graph is None:
        _investment_graph = build_investment_graph()
    return _investment_graph


async def run_agent_workflow(query: str) -> dict:
    """투자 판단 워크플로우 단일 진입점.

    입력: query (사용자 투자 판단 질의 텍스트)
    출력: final_answer / analysis / retrieved_data 딕셔너리

    흐름: START → Orchestrator → [Retrieval | Analysis | Synthesis]* → END
    """
    logger.info("[InvestmentGraph] run_agent_workflow start query=%s", query[:80])
    await aemit(f"[InvestmentGraph] {'='*50}")
    await aemit(f"[InvestmentGraph] 워크플로우 시작 | query={query[:80]}")
    await aemit(f"[InvestmentGraph] {'='*50}")

    graph = get_investment_graph()

    initial_state: InvestmentAgentState = {
        "query": query,
        "parsed_query": None,
        "retrieved_data": None,
        "news_signal": None,
        "youtube_signal": None,
        "investment_verdict": None,
        "analysis": None,
        "final_answer": None,
        "next_agent": None,
        "iteration_count": 0,
        "messages": [],
    }

    result = await graph.ainvoke(initial_state)

    logger.info(
        "[InvestmentGraph] complete final_answer=%s",
        str(result.get("final_answer", ""))[:80],
    )
    await aemit(f"[InvestmentGraph] {'='*50}")
    await aemit(f"[InvestmentGraph] 워크플로우 완료")

    return {
        "query": query,
        "retrieved_data": result.get("retrieved_data"),
        "analysis": result.get("analysis"),
        "final_answer": result.get("final_answer"),
    }
