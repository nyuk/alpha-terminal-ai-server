import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.domains.account.adapter.inbound.api.account_router import router as account_router
from app.domains.account.infrastructure.orm.account_orm import AccountORM  # noqa: F401
from app.domains.auth.adapter.inbound.api.auth_router import router as auth_router
from app.domains.auth.adapter.inbound.api.authentication_router import router as authentication_router
from app.domains.kakao_auth.adapter.inbound.api.kakao_authentication_router import router as kakao_authentication_router
from app.domains.news_search.adapter.inbound.api.news_search_router import router as news_search_router
from app.domains.news_search.adapter.inbound.api.saved_article_router import router as saved_article_router
from app.domains.news_search.infrastructure.orm.saved_article_orm import SavedArticleORM  # noqa: F401
from app.domains.news_search.infrastructure.orm.saved_article_content_orm import SavedArticleContentORM  # noqa: F401
from app.domains.news_search.infrastructure.orm.investment_news_orm import InvestmentNewsORM  # noqa: F401
from app.domains.news_search.infrastructure.orm.investment_news_content_orm import InvestmentNewsContentORM  # noqa: F401
from app.domains.pipeline.adapter.inbound.api.pipeline_router import router as pipeline_router
from app.domains.pipeline.infrastructure.orm.analysis_log_orm import AnalysisLogORM  # noqa: F401
from app.domains.board.adapter.inbound.api.board_router import router as board_router
from app.domains.board.infrastructure.orm.board_orm import BoardORM  # noqa: F401
from app.domains.post.adapter.inbound.api.post_router import router as post_router
from app.domains.post.infrastructure.orm.post_orm import PostORM  # noqa: F401
from app.domains.stock.adapter.inbound.api.stock_router import router as stock_router
from app.domains.stock.infrastructure.orm.stock_orm import StockORM  # noqa: F401
from app.domains.stock_analyzer.adapter.inbound.api.analyzer_router import router as analyzer_router
from app.domains.stock_collector.adapter.inbound.api.collector_router import router as collector_router
from app.domains.stock_collector.infrastructure.orm.raw_article_orm import RawArticleORM  # noqa: F401
from app.domains.stock_normalizer.adapter.inbound.api.normalizer_router import router as normalizer_router
from app.domains.watchlist.adapter.inbound.api.watchlist_router import router as watchlist_router
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM  # noqa: F401
from app.domains.card_share.adapter.inbound.api.card_share_router import router as card_share_router
from app.domains.public.adapter.inbound.api.public_router import router as public_router
from app.domains.market_video.adapter.inbound.api.youtube_router import router as youtube_router
from app.domains.market_video.adapter.inbound.api.market_video_collect_router import router as market_video_collect_router
from app.domains.market_video.adapter.inbound.api.video_comment_router import router as video_comment_router
from app.domains.market_video.adapter.inbound.api.noun_extraction_router import router as noun_extraction_router
from app.domains.market_video.infrastructure.orm.market_video_orm import MarketVideoORM  # noqa: F401
from app.domains.youtube.adapter.inbound.api.youtube_router import router as market_video_router
from app.domains.youtube.infrastructure.orm.youtube_video_orm import YouTubeVideoORM  # noqa: F401
from app.domains.youtube.infrastructure.orm.youtube_comment_orm import YouTubeCommentORM  # noqa: F401
from app.domains.card_share.infrastructure.orm.shared_card_orm import SharedCardORM  # noqa: F401
from app.domains.card_share.infrastructure.orm.card_like_orm import CardLikeORM  # noqa: F401
from app.domains.card_share.infrastructure.orm.card_comment_orm import CardCommentORM  # noqa: F401
from app.domains.stock_theme.adapter.inbound.api.stock_theme_router import router as stock_theme_router
from app.domains.stock_theme.infrastructure.orm.stock_theme_orm import StockThemeORM  # noqa: F401
from app.domains.user_profile.infrastructure.orm.user_profile_orm import UserProfileORM  # noqa: F401
from app.domains.user_profile.infrastructure.orm.user_interaction_orm import UserInteractionORM  # noqa: F401
from app.domains.user_profile.adapter.inbound.api.user_profile_router import router as user_profile_router
from app.domains.market_analysis.adapter.inbound.api.market_analysis_router import router as market_analysis_router
from app.domains.investment.adapter.inbound.api.investment_router import router as investment_router
from app.domains.admin.adapter.inbound.api.admin_router import router as admin_router
from app.domains.notification.adapter.inbound.api.notification_router import router as notification_router
from app.domains.analytics.adapter.inbound.api.analytics_router import router as analytics_router
from app.domains.analytics.infrastructure.orm.event_orm import EventORM  # noqa: F401
from app.domains.notification.infrastructure.orm.notification_orm import NotificationORM  # noqa: F401
from app.domains.investment.infrastructure.orm.investment_youtube_log_orm import InvestmentYouTubeLogORM  # noqa: F401
from app.domains.investment.infrastructure.orm.investment_youtube_video_orm import InvestmentYouTubeVideoORM  # noqa: F401
from app.domains.investment.infrastructure.orm.investment_youtube_comment_orm import InvestmentYouTubeCommentORM  # noqa: F401
from app.domains.investment.infrastructure.orm.analysis_cache_orm import AnalysisCacheORM  # noqa: F401
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.database.pg_session import PgBase, pg_engine, check_pg_health
from app.infrastructure.external.serp_client import SerpClient
from app.infrastructure.scheduler.pipeline_scheduler import start_scheduler, stop_scheduler
from app.infrastructure.scheduler.profile_update_scheduler import start_profile_scheduler, stop_profile_scheduler
from app.infrastructure.scheduler.proactive_recommendation_scheduler import start_proactive_recommendation_scheduler, stop_proactive_recommendation_scheduler

logger = logging.getLogger(__name__)

settings: Settings = get_settings()


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    # BL-BE-84: PG create_all 을 lifespan startup 으로 이동 (모듈 레벨 실행 제거)
    # TODO: PG Alembic cutover 완료 후 아래 create_all 블록 제거하고 alembic upgrade head 로 대체
    try:
        PgBase.metadata.create_all(bind=pg_engine)
    except Exception:
        logger.exception(
            "PostgreSQL schema init failed — JSONB article content store unavailable. "
            "Check PG_* env and that Postgres is reachable from the API container (not host localhost unless network_mode=host)."
        )

    check_pg_health()
    from app.domains.pipeline.adapter.inbound.api.pipeline_router import run_pipeline_job
    start_scheduler(run_pipeline_job)
    start_profile_scheduler()
    start_proactive_recommendation_scheduler()
    yield
    stop_scheduler()
    stop_profile_scheduler()
    stop_proactive_recommendation_scheduler()
    # BL-BE-85: SerpClient httpx.Client 커넥션 풀 명시적 종료
    SerpClient.close()


app = FastAPI(debug=settings.debug, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_allowed_frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(account_router)
app.include_router(auth_router)
app.include_router(authentication_router)
app.include_router(kakao_authentication_router)
app.include_router(board_router)
app.include_router(post_router)
app.include_router(news_search_router)
app.include_router(saved_article_router)
app.include_router(watchlist_router)
app.include_router(collector_router)
app.include_router(normalizer_router)
app.include_router(stock_router)
app.include_router(analyzer_router)
app.include_router(pipeline_router)
app.include_router(card_share_router)
app.include_router(public_router)
app.include_router(youtube_router)
app.include_router(market_video_collect_router)
app.include_router(video_comment_router)
app.include_router(noun_extraction_router)
app.include_router(market_video_router)
app.include_router(stock_theme_router)
app.include_router(market_analysis_router)
app.include_router(investment_router)
app.include_router(admin_router)
app.include_router(notification_router)
app.include_router(analytics_router)
app.include_router(user_profile_router)


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=33333)
