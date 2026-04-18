from app.domains.user_profile.application.port.user_profile_repository_port import UserProfileRepositoryPort
from app.domains.user_profile.application.request.save_recently_viewed_request import SaveRecentlyViewedRequest
from app.domains.user_profile.application.response.user_profile_response import SaveRecentlyViewedResponse
from app.domains.user_profile.domain.entity.user_interaction import UserInteraction, InteractionType


class SaveRecentlyViewedUseCase:
    MAX_RECENTLY_VIEWED = 10

    def __init__(self, repository: UserProfileRepositoryPort):
        self._repository = repository

    def execute(self, account_id: int, request: SaveRecentlyViewedRequest) -> SaveRecentlyViewedResponse:
        interaction = UserInteraction(
            account_id=account_id,
            symbol=request.symbol,
            name=request.name,
            market=request.market,
            interaction_type=InteractionType.CLICK,
            count=1,
        )
        saved = self._repository.upsert_recently_viewed(interaction)
        self._repository.enforce_max_recently_viewed(account_id, self.MAX_RECENTLY_VIEWED)

        return SaveRecentlyViewedResponse(
            symbol=saved.symbol,
            name=saved.name or "",
            market=saved.market,
            viewed_at=saved.created_at,
        )
