from app.domains.news_analyzer.application.request.analyze_article_request import AnalyzeArticleRequest
from app.domains.news_analyzer.application.response.analyze_article_response import AnalyzeArticleResponse
from app.domains.news_analyzer.application.usecase.article_analysis_port import ArticleAnalysisPort
from app.domains.news_analyzer.application.usecase.exceptions import ArticleNotFoundError, EmptyContentError
from app.domains.news_analyzer.application.usecase.saved_article_query_port import SavedArticleQueryPort


class AnalyzeArticleUseCase:
    def __init__(
        self,
        article_query: SavedArticleQueryPort,
        analyzer: ArticleAnalysisPort,
    ):
        self._article_query = article_query
        self._analyzer = analyzer

    def execute(self, request: AnalyzeArticleRequest) -> AnalyzeArticleResponse:
        article = self._article_query.find_by_id(request.article_id)
        if article is None:
            raise ArticleNotFoundError("기사를 찾을 수 없습니다.")

        if not article.content or not article.content.strip():
            raise EmptyContentError("기사 본문이 비어 있어 분석할 수 없습니다.")

        result = self._analyzer.analyze(article.content)

        return AnalyzeArticleResponse(
            article_id=request.article_id,
            keywords=result.keywords,
            sentiment=result.sentiment.value,
            sentiment_score=result.sentiment_score,
        )
