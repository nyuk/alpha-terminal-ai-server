from logging.config import fileConfig
import os
from urllib.parse import quote_plus

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.infrastructure.config.settings import get_settings
from app.infrastructure.database.session import Base

# MySQL Base metadata에 포함될 ORM을 전부 import 해야 autogenerate가 변경을 감지한다.
from app.domains.account.infrastructure.orm.account_orm import AccountORM  # noqa: F401
from app.domains.board.infrastructure.orm.board_orm import BoardORM  # noqa: F401
from app.domains.card_share.infrastructure.orm.card_comment_orm import CardCommentORM  # noqa: F401
from app.domains.card_share.infrastructure.orm.card_like_orm import CardLikeORM  # noqa: F401
from app.domains.card_share.infrastructure.orm.shared_card_orm import SharedCardORM  # noqa: F401
from app.domains.investment.infrastructure.orm.investment_youtube_log_orm import InvestmentYouTubeLogORM  # noqa: F401
from app.domains.investment.infrastructure.orm.investment_youtube_video_orm import InvestmentYouTubeVideoORM  # noqa: F401
from app.domains.market_video.infrastructure.orm.market_video_orm import MarketVideoORM  # noqa: F401
from app.domains.news_search.infrastructure.orm.investment_news_orm import InvestmentNewsORM  # noqa: F401
from app.domains.news_search.infrastructure.orm.saved_article_orm import SavedArticleORM  # noqa: F401
from app.domains.notification.infrastructure.orm.notification_orm import NotificationORM  # noqa: F401
from app.domains.pipeline.infrastructure.orm.analysis_log_orm import AnalysisLogORM  # noqa: F401
from app.domains.post.infrastructure.orm.post_orm import PostORM  # noqa: F401
from app.domains.stock.infrastructure.orm.stock_orm import StockORM  # noqa: F401
from app.domains.stock_collector.infrastructure.orm.raw_article_orm import RawArticleORM  # noqa: F401
from app.domains.stock_theme.infrastructure.orm.stock_theme_orm import StockThemeORM  # noqa: F401
from app.domains.user_profile.infrastructure.orm.user_interaction_orm import UserInteractionORM  # noqa: F401
from app.domains.user_profile.infrastructure.orm.user_profile_orm import UserProfileORM  # noqa: F401
from app.domains.watchlist.infrastructure.orm.watchlist_item_orm import WatchlistItemORM  # noqa: F401
from app.domains.youtube.infrastructure.orm.youtube_comment_orm import YouTubeCommentORM  # noqa: F401
from app.domains.youtube.infrastructure.orm.youtube_video_orm import YouTubeVideoORM  # noqa: F401
from app.domains.analytics.infrastructure.orm.event_orm import EventORM  # noqa: F401

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    settings = get_settings()
    db_name = os.getenv("ALEMBIC_MYSQL_DATABASE", settings.mysql_database)
    return (
        f"mysql+pymysql://{settings.mysql_user}:{quote_plus(settings.mysql_password)}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{db_name}"
    )


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
