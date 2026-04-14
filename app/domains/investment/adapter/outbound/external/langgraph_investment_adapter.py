from app.domains.investment.application.usecase.investment_decision_port import InvestmentDecisionPort
from app.domains.investment.domain.entity.investment_decision import InvestmentDecision


class LangGraphInvestmentAdapter(InvestmentDecisionPort):
    """LangGraph 투자 판단 멀티 에이전트 워크플로우 Outbound Adapter.

    워크플로우: Orchestrator → Retrieval → Analysis → Synthesis
    단일 진입점 run_agent_workflow를 통해 실행한다.
    """

    async def decide(self, query: str) -> InvestmentDecision:
        from app.domains.investment.infrastructure.langgraph.investment_graph_builder import run_agent_workflow

        result = await run_agent_workflow(query)
        answer = (
            result.get("final_answer")
            or result.get("analysis")
            or "투자 판단 결과를 생성하지 못했습니다."
        )
        return InvestmentDecision(answer=answer)
