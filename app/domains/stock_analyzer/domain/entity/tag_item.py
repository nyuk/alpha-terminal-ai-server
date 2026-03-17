from dataclasses import dataclass
from enum import Enum


class TagCategory(str, Enum):
    CAPITAL = "CAPITAL"         # 자본 변동 (증자, 감자, 배당)
    EARNINGS = "EARNINGS"       # 실적 (매출, 영업이익)
    PRODUCT = "PRODUCT"         # 제품/서비스
    MANAGEMENT = "MANAGEMENT"   # 경영진/조직 변경
    INDUSTRY = "INDUSTRY"       # 산업/시장 동향
    RISK = "RISK"               # 리스크 (소송, 규제, 사고)
    OTHER = "OTHER"             # 기타


@dataclass
class TagItem:
    label: str
    category: TagCategory
