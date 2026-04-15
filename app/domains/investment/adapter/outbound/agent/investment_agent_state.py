import operator
from typing import Annotated, List, Optional

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

# 다음 실행할 에이전트를 결정하는 Orchestrator 라우팅 키
NEXT_RETRIEVAL = "retrieval"
NEXT_ANALYSIS = "analysis"
NEXT_SYNTHESIS = "synthesis"
NEXT_END = "end"


class InvestmentAgentState(TypedDict):
    """투자 판단 멀티 에이전트 워크플로우 공유 상태.

    query           : 사용자 원본 투자 질의
    parsed_query    : Query Parser 파싱 결과 (company / intent / required_data)
    retrieved_data  : Retrieval Agent가 수집한 원천 데이터 (뉴스, 종목 정보 등)
    analysis        : Analysis Agent가 생성한 인사이트 (종목 전망, 리스크, 투자 포인트)
    final_answer    : Synthesis Agent가 생성한 최종 사용자 응답
    next_agent      : Orchestrator가 결정한 다음 실행 에이전트 키
    iteration_count : 반복 횟수 (무한루프 방지)
    messages        : 노드 간 누적 메시지 히스토리 (Annotated[List, add]로 자동 병합)
    """

    query: str
    parsed_query: Optional[dict]        # ParsedQuery: company / intent / required_data
    retrieved_data: Optional[str]
    news_signal: Optional[dict]         # NewsSentimentMetrics
    youtube_signal: Optional[dict]      # YouTubeSentimentMetrics
    investment_verdict: Optional[dict]  # InvestmentDecision
    analysis: Optional[str]
    final_answer: Optional[str]
    next_agent: Optional[str]
    iteration_count: int
    messages: Annotated[List[BaseMessage], operator.add]
