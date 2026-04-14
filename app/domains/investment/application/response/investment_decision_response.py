from pydantic import BaseModel


class InvestmentDecisionResponse(BaseModel):
    answer: str
