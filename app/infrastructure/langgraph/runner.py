"""LangGraph 그래프 실행 진입점.

외부 코드는 run_agent_graph() 단일 함수만 호출한다.
스모크 테스트는 smoke_test()로 수행한다.
"""
import logging
from typing import Optional

from langchain_core.messages import HumanMessage

from app.infrastructure.langgraph.graph_builder import build_market_analysis_graph
from app.infrastructure.langgraph.state import AgentState

logger = logging.getLogger(__name__)

_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_market_analysis_graph()
    return _graph


def run_agent_graph(
    task: str,
    account_id: Optional[int] = None,
    watchlist_context: str = "",
) -> str:
    """멀티 에이전트 그래프 단일 진입점.

    Args:
        task: 사용자 분석 요청 문자열
        account_id: 사용자 식별자 (None 허용 — 스모크 실행 등)
        watchlist_context: DB에서 조합된 관심종목 컨텍스트 텍스트

    Returns:
        Reviewer 노드가 확정한 최종 출력 문자열

    Raises:
        RuntimeError: 노드 실행 중 복구 불가능한 에러 발생 시
    """
    logger.info("[Runner] 그래프 실행 시작 account_id=%s task=%.80s", account_id, task)
    graph = _get_graph()

    initial_state: AgentState = {
        "messages": [HumanMessage(content=task)],
        "account_id": account_id,
        "task": task,
        "watchlist_context": watchlist_context,
        "current_node": "",
        "final_output": None,
        "error": None,
    }

    result = graph.invoke(initial_state)

    if result.get("error"):
        logger.error("[Runner] 그래프 에러 종료 error=%s", result["error"])
        raise RuntimeError(result["error"])

    output: str = result.get("final_output") or ""
    logger.info("[Runner] 그래프 실행 완료 output_length=%d", len(output))
    return output


def smoke_test() -> bool:
    """인프라 구성 검증용 스모크 실행.

    "안녕" 입력으로 그래프를 1회 실행하여 노드 전체가 정상 동작하는지 확인한다.

    Returns:
        정상 완료 시 True, 실패 시 False
    """
    try:
        result = run_agent_graph(task="안녕", account_id=None, watchlist_context="")
        logger.info("[SmokeTest] 통과 output=%.100s", result)
        return True
    except Exception as e:
        logger.error("[SmokeTest] 실패: %s", e)
        return False
