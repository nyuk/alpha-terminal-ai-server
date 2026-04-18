from app.domains.user_profile.application.port.user_profile_repository_port import UserProfileRepositoryPort
from app.domains.user_profile.application.port.watchlist_summary_port import WatchlistSummaryPort
from app.domains.user_profile.application.response.user_profile_response import (
    UserProfileResponse,
    InteractionHistoryResponse,
    LikeHistoryItem,
    WatchlistSummaryItem,
    RecentlyViewedItem,
    ClickedCardItem,
)
from app.domains.user_profile.domain.entity.user_interaction import InteractionType
from app.domains.user_profile.domain.entity.user_profile import UserProfile


class GetUserProfileUseCase:
    def __init__(
        self,
        repository: UserProfileRepositoryPort,
        watchlist_port: WatchlistSummaryPort,
    ):
        self._repository = repository
        self._watchlist_port = watchlist_port

    def execute(self, account_id: int) -> UserProfileResponse:
        profile = self._repository.find_by_account_id(account_id)
        if profile is None:
            profile = UserProfile(account_id=account_id)

        interactions = self._repository.find_interactions_by_account_id(account_id)

        like_map: dict[str, int] = {}
        comments: list[str] = []
        recently_viewed: list[RecentlyViewedItem] = []
        clicked_cards_map: dict[str, int] = {}
        seen_click_symbols: set[str] = set()

        for interaction in interactions:
            if interaction.interaction_type == InteractionType.LIKE:
                like_map[interaction.symbol] = like_map.get(interaction.symbol, 0) + interaction.count
            elif interaction.interaction_type == InteractionType.COMMENT and interaction.content:
                comments.append(interaction.content)
            elif interaction.interaction_type == InteractionType.CLICK:
                if interaction.symbol not in seen_click_symbols:
                    recently_viewed.append(RecentlyViewedItem(
                        symbol=interaction.symbol,
                        name=interaction.name,
                        market=interaction.market,
                        viewed_at=interaction.created_at,
                    ))
                    seen_click_symbols.add(interaction.symbol)
                clicked_cards_map[interaction.symbol] = (
                    clicked_cards_map.get(interaction.symbol, 0) + interaction.count
                )

        watchlist_orm_items = self._watchlist_port.find_all(account_id=account_id)
        watchlist = [
            WatchlistSummaryItem(symbol=item.symbol, name=item.name, market=item.market)
            for item in watchlist_orm_items
        ]

        likes = [LikeHistoryItem(symbol=s, count=c) for s, c in like_map.items()]
        clicked_cards = [ClickedCardItem(symbol=s, count=c) for s, c in clicked_cards_map.items()]

        return UserProfileResponse(
            account_id=profile.account_id,
            watchlist=watchlist,
            recently_viewed=recently_viewed[:10],
            clicked_cards=clicked_cards,
            preferred_stocks=profile.preferred_stocks,
            interaction_history=InteractionHistoryResponse(likes=likes, comments=comments),
            interests_text=profile.interests_text,
        )
