from app.domains.news_search.application.request.save_article_request import SaveArticleRequest
from app.domains.news_search.application.response.save_article_response import SaveArticleResponse
from app.domains.news_search.application.usecase.article_content_port import ArticleContentPort
from app.domains.news_search.application.usecase.saved_article_repository_port import SavedArticleRepositoryPort
from app.domains.news_search.domain.entity.saved_article import SavedArticle


class SaveArticleUseCase:
    def __init__(
        self,
        repository: SavedArticleRepositoryPort,
        content_fetcher: ArticleContentPort,
    ):
        self._repository = repository
        self._content_fetcher = content_fetcher

    def execute(self, request: SaveArticleRequest) -> SaveArticleResponse:
        existing = self._repository.find_by_link(request.link)
        if existing:
            raise ValueError("이미 저장된 기사입니다.")

        content = self._content_fetcher.fetch_content(request.link)

        article = SavedArticle(
            title=request.title,
            link=request.link,
            source=request.source,
            snippet=request.snippet,
            published_at=request.published_at,
            content=content,
        )

        saved = self._repository.save(article)

        return SaveArticleResponse(
            id=saved.id,
            title=saved.title,
            link=saved.link,
            source=saved.source,
            snippet=saved.snippet,
            content=saved.content,
            published_at=saved.published_at,
            saved_at=saved.saved_at,
        )
