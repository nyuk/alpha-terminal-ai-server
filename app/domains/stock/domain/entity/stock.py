from dataclasses import dataclass
from typing import Optional


@dataclass
class Stock:
    symbol: str        # 종목코드 (6자리)
    name: str          # 회사명
    market: str        # 시장 구분 (Y:유가증권, K:코스닥, N:코넥스, E:ETC)
    corp_code: str     # DART 고유번호
    id: Optional[int] = None
