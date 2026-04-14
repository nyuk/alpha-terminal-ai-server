from abc import ABC, abstractmethod

from app.domains.investment.domain.entity.investment_decision import InvestmentDecision


class InvestmentDecisionPort(ABC):
    """투자 판단 외부 시스템 Port."""

    @abstractmethod
    async def decide(self, query: str) -> InvestmentDecision:
        """질의를 받아 투자 판단 결과를 반환한다."""
