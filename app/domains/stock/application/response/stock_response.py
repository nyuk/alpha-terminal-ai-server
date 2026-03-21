from pydantic import BaseModel


class StockResponse(BaseModel):
    symbol: str
    name: str
    market: str
