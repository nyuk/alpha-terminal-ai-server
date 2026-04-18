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
from app.domains.market_analysis.adapter.inbound.api.market_analysis_router import router as market_analysis_router
from app.domains.investment.adapter.inbound.api.investment_router import router as investment_router
from app.domains.admin.adapter.inbound.api.admin_router import router as admin_router
from app.domains.notification.adapter.inbound.api.notification_router import router as notification_router
from app.domains.notification.infrastructure.orm.notification_orm import NotificationORM  # noqa: F401
from app.domains.investment.infrastructure.orm.investment_youtube_log_orm import InvestmentYouTubeLogORM  # noqa: F401
from app.domains.investment.infrastructure.orm.investment_youtube_video_orm import InvestmentYouTubeVideoORM  # noqa: F401
from app.domains.investment.infrastructure.orm.investment_youtube_comment_orm import InvestmentYouTubeCommentORM  # noqa: F401
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.database.session import Base, engine
from app.infrastructure.database.pg_session import PgBase, pg_engine, check_pg_health
from app.infrastructure.scheduler.pipeline_scheduler import start_scheduler, stop_scheduler
from app.infrastructure.scheduler.profile_update_scheduler import start_profile_scheduler, stop_profile_scheduler
from app.infrastructure.scheduler.proactive_recommendation_scheduler import start_proactive_recommendation_scheduler, stop_proactive_recommendation_scheduler

logger = logging.getLogger(__name__)

settings: Settings = get_settings()

Base.metadata.create_all(bind=engine)
try:
    PgBase.metadata.create_all(bind=pg_engine)
except Exception:
    logger.exception(
        "PostgreSQL schema init failed — JSONB article content store unavailable. "
        "Check PG_* env and that Postgres is reachable from the API container (not host localhost unless network_mode=host)."
    )


def _run_column_migrations():
    """create_all이 처리하지 못하는 기존 테이블 컬럼 추가를 수동으로 실행."""
    from sqlalchemy import text

    def _column_exists(conn, table: str, column: str) -> bool:
        row = conn.execute(text(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND COLUMN_NAME = :c"
        ), {"t": table, "c": column}).scalar()
        return row > 0

    def _index_exists(conn, table: str, index: str) -> bool:
        row = conn.execute(text(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.STATISTICS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t AND INDEX_NAME = :i"
        ), {"t": table, "i": index}).scalar()
        return row > 0

    with engine.connect() as conn:
        # accounts — role (BL-BE-68)
        if not _column_exists(conn, "accounts", "role"):
            try:
                conn.execute(text(
                    "ALTER TABLE accounts ADD COLUMN role VARCHAR(10) NOT NULL DEFAULT 'NORMAL'"
                ))
                conn.commit()
                logger.info("[migration] accounts.role 추가 완료")
            except Exception as e:
                logger.warning(f"[migration] accounts.role 추가 실패: {e}")

        # accounts — is_watchlist_public
        if not _column_exists(conn, "accounts", "is_watchlist_public"):
            try:
                conn.execute(text(
                    "ALTER TABLE accounts ADD COLUMN is_watchlist_public BOOLEAN NOT NULL DEFAULT TRUE"
                ))
                conn.commit()
                logger.info("[migration] accounts.is_watchlist_public 추가 완료")
            except Exception as e:
                logger.warning(f"[migration] accounts.is_watchlist_public 추가 실패: {e}")

        # saved_articles — account_id 추가
        if not _column_exists(conn, "saved_articles", "account_id"):
            try:
                conn.execute(text(
                    "ALTER TABLE saved_articles ADD COLUMN account_id INT NOT NULL DEFAULT 0"
                ))
                conn.commit()
                logger.info("[migration] saved_articles.account_id 추가 완료")
            except Exception as e:
                logger.warning(f"[migration] saved_articles.account_id 추가 실패: {e}")

        # saved_articles — content 컬럼 제거
        if _column_exists(conn, "saved_articles", "content"):
            try:
                conn.execute(text("ALTER TABLE saved_articles DROP COLUMN content"))
                conn.commit()
                logger.info("[migration] saved_articles.content 제거 완료")
            except Exception as e:
                logger.warning(f"[migration] saved_articles.content 제거 실패: {e}")

        # saved_articles — 구 link_hash 단독 인덱스 제거
        if _index_exists(conn, "saved_articles", "link_hash"):
            try:
                conn.execute(text("ALTER TABLE saved_articles DROP INDEX link_hash"))
                conn.commit()
                logger.info("[migration] saved_articles.link_hash 인덱스 제거 완료")
            except Exception as e:
                logger.warning(f"[migration] saved_articles.link_hash 인덱스 제거 실패: {e}")

        # saved_articles — (account_id, link_hash) unique 인덱스 추가
        if not _index_exists(conn, "saved_articles", "uq_saved_articles_account_link"):
            try:
                conn.execute(text(
                    "ALTER TABLE saved_articles "
                    "ADD UNIQUE INDEX uq_saved_articles_account_link (account_id, link_hash)"
                ))
                conn.commit()
                logger.info("[migration] saved_articles unique constraint 추가 완료")
            except Exception as e:
                logger.warning(f"[migration] saved_articles unique constraint 추가 실패: {e}")

        # user_interactions — name, market (BL-BE-62)
        if not _column_exists(conn, "user_interactions", "name"):
            try:
                conn.execute(text("ALTER TABLE user_interactions ADD COLUMN name VARCHAR(100)"))
                conn.commit()
                logger.info("[migration] user_interactions.name 추가 완료")
            except Exception as e:
                logger.warning(f"[migration] user_interactions.name 추가 실패: {e}")

        if not _column_exists(conn, "user_interactions", "market"):
            try:
                conn.execute(text("ALTER TABLE user_interactions ADD COLUMN market VARCHAR(20)"))
                conn.commit()
                logger.info("[migration] user_interactions.market 추가 완료")
            except Exception as e:
                logger.warning(f"[migration] user_interactions.market 추가 실패: {e}")


_run_column_migrations()


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    check_pg_health()
    from app.domains.pipeline.adapter.inbound.api.pipeline_router import run_pipeline_job
    start_scheduler(run_pipeline_job)
    start_profile_scheduler()
    start_proactive_recommendation_scheduler()
    yield
    stop_scheduler()
    stop_profile_scheduler()
    stop_proactive_recommendation_scheduler()


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


@app.get("/")
async def root():
    return {"message": "Hello World"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=33333)
