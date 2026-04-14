from pydantic import BaseModel, Field


class InvestmentDecisionRequest(BaseModel):
    query: str = Field(..., min_length=1, description="투자 판단 질의 텍스트")
