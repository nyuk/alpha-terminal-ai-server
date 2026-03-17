from fastapi import FastAPI

from app.domains.news_search.adapter.inbound.api.news_search_router import router as news_search_router
from app.domains.stock_analyzer.adapter.inbound.api.analyzer_router import router as analyzer_router
from app.domains.stock_normalizer.adapter.inbound.api.normalizer_router import router as normalizer_router
from app.domains.stock_collector.adapter.inbound.api.collector_router import router as collector_router
from app.domains.stock_collector.infrastructure.orm.raw_article_orm import RawArticleORM  # noqa: F401
from app.domains.news_search.adapter.inbound.api.saved_article_router import router as saved_article_router
from app.domains.news_search.infrastructure.orm.saved_article_orm import SavedArticleORM  # noqa: F401
from app.domains.post.adapter.inbound.api.post_router import router as post_router
from app.domains.post.infrastructure.orm.post_orm import PostORM  # noqa: F401
from app.domains.watchlist.adapter.inbound.api.watchlist_router import router as watchlist_router
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM  # noqa: F401
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.database.session import Base, engine

settings: Settings = get_settings()

Base.metadata.create_all(bind=engine)

app = FastAPI(debug=settings.debug)

app.include_router(post_router)
app.include_router(news_search_router)
app.include_router(saved_article_router)
app.include_router(watchlist_router)
app.include_router(collector_router)
app.include_router(normalizer_router)
app.include_router(analyzer_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=33333)
