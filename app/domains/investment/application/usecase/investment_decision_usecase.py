from app.domains.investment.application.usecase.investment_decision_port import InvestmentDecisionPort
from app.domains.investment.domain.entity.investment_decision import InvestmentDecision


class InvestmentDecisionUseCase:
    """투자 판단 요청 UseCase."""

    def __init__(self, decision_port: InvestmentDecisionPort) -> None:
        self._port = decision_port

    async def execute(self, query: str) -> InvestmentDecision:
        return await self._port.decide(query)
