import logging
from typing import List

from app.domains.market_analysis.adapter.outbound.persistence.market_data_repository_impl import (
    MarketDataRepositoryImpl,
)
from app.domains.market_analysis.adapter.outbound.external.langchain_qa_adapter import LangChainQAAdapter
from app.domains.market_analysis.domain.service.context_builder_service import (
    ContextBuilderService,
    WatchlistContext,
)
from app.domains.notification.adapter.outbound.persistence.notification_repository_impl import (
    NotificationRepositoryImpl,
)
from app.domains.notification.domain.entity.notification import Notification
from app.domains.user_profile.adapter.outbound.persistence.user_profile_repository_impl import (
    UserProfileRepositoryImpl,
)

logger = logging.getLogger(__name__)

_QUESTION = (
    "관심종목 현황을 AI_BRIEFING 형식으로 간략히 요약해주세요. "
    "주목할 만한 테마 변화, 리스크 요인, 매수/매도/보유 추천과 확인할 조건을 알려주세요. "
    "필요하면 명확한 판단을 제시하되 근거와 조건 중심으로 정리해주세요."
)


class RunProactiveRecommendationUseCase:
    def __init__(
        self,
        market_repo: MarketDataRepositoryImpl,
        profile_repo: UserProfileRepositoryImpl,
        notification_repo: NotificationRepositoryImpl,
        qa: LangChainQAAdapter,
    ):
        self._market_repo = market_repo
        self._profile_repo = profile_repo
        self._notification_repo = notification_repo
        self._qa = qa
        self._context_builder = ContextBuilderService()

    def execute(self) -> int:
        account_ids = self._profile_repo.find_all_account_ids()
        sent = 0

        for account_id in account_ids:
            try:
                sent += self._process_account(account_id)
            except Exception:
                logger.exception("[ProactiveRecommendation] account_id=%d 처리 오류", account_id)

        return sent

    def _process_account(self, account_id: int) -> int:
        watchlist = self._market_repo.get_watchlist(account_id)
        if not watchlist:
            return 0

        codes = [s.symbol for s in watchlist]
        themes = self._market_repo.get_stock_themes_by_codes(codes)
        themes_map = {t.code: t.themes for t in themes}

        contexts = [
            WatchlistContext(symbol=s.symbol, name=s.name, themes=themes_map.get(s.symbol, []))
            for s in watchlist
        ]

        profile = self._profile_repo.find_by_account_id(account_id)
        context = self._context_builder.build(contexts, user_profile=profile)

        answer = self._qa.ask(_QUESTION, context)
        if not answer.in_scope or not answer.answer:
            return 0

        stock_names = ", ".join(s.name for s in watchlist[:3])
        if len(watchlist) > 3:
            stock_names += f" 외 {len(watchlist) - 3}종목"

        notification = Notification(
            user_id=account_id,
            title=f"[오늘의 관심종목 브리핑] {stock_names}",
            body=answer.answer[:500],
        )
        self._notification_repo.save(notification)
        logger.debug("[ProactiveRecommendation] account_id=%d 알림 저장 완료", account_id)
        return 1
