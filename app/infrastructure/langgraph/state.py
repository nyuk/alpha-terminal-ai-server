"""LangGraph 멀티 에이전트 공통 State 타입 정의."""
from typing import Annotated, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """멀티 에이전트 그래프 공통 실행 컨텍스트.

    messages  : 에이전트 간 누적 대화 히스토리 (add_messages 리듀서로 append)
    account_id: 요청한 사용자 식별자 (None이면 비인증 스모크 실행)
    task      : 그래프에 전달된 원본 요청 문자열
    watchlist_context: DB에서 조합된 관심종목 컨텍스트 텍스트
    current_node     : 마지막으로 실행된 노드 이름 (디버깅용)
    final_output     : Reviewer 노드가 확정한 최종 출력
    error            : 노드 실행 중 발생한 에러 메시지 (있으면 조건부 라우팅으로 조기 종료)
    """

    messages: Annotated[list[BaseMessage], add_messages]
    account_id: Optional[int]
    task: str
    watchlist_context: str
    current_node: str
    final_output: Optional[str]
    error: Optional[str]
