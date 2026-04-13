"""LangGraph 멀티 에이전트 그래프 빌더.

그래프 구조:
    START → planner → researcher → analyst →(조건부)→ reviewer → END
                                            ↘ error →            END
"""
import logging

from langgraph.graph import END, START, StateGraph

from app.infrastructure.langgraph.nodes.analyst import analyst_node
from app.infrastructure.langgraph.nodes.planner import planner_node
from app.infrastructure.langgraph.nodes.researcher import researcher_node
from app.infrastructure.langgraph.nodes.reviewer import reviewer_node
from app.infrastructure.langgraph.state import AgentState

logger = logging.getLogger(__name__)


def _route_from_analyst(state: AgentState) -> str:
    """analyst 결과에 에러가 있으면 조기 종료, 없으면 reviewer로 진행."""
    if state.get("error"):
        logger.warning("[Router] analyst 에러 감지 → END (error=%s)", state["error"])
        return "end"
    return "reviewer"


def build_market_analysis_graph():
    """관심종목 분석용 멀티 에이전트 그래프를 빌드하여 반환한다."""
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("reviewer", reviewer_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "researcher")
    builder.add_edge("researcher", "analyst")
    builder.add_conditional_edges(
        "analyst",
        _route_from_analyst,
        {"reviewer": "reviewer", "end": END},
    )
    builder.add_edge("reviewer", END)

    graph = builder.compile()
    logger.info("[GraphBuilder] 멀티 에이전트 그래프 빌드 완료")
    return graph
