from pydantic import BaseModel


class AnalyzeArticleRequest(BaseModel):
    article_id: str
    stock_symbol: str
    source_type: str       # DISCLOSURE | NEWS
    source_name: str       # DART | NAVER_NEWS
    title: str
    body: str
    category: str          # DISCLOSURE_CAPITAL | DISCLOSURE_EARNINGS | ... | NEWS
    lang: str = "ko"
