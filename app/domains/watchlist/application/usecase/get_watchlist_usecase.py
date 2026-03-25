from typing import List, Optional

from app.domains.watchlist.application.response.watchlist_response import WatchlistItemResponse
from app.domains.watchlist.application.usecase.watchlist_repository_port import WatchlistRepositoryPort


class GetWatchlistUseCase:
    def __init__(self, repository: WatchlistRepositoryPort):
        self._repository = repository

    def execute(self, account_id: Optional[int] = None) -> List[WatchlistItemResponse]:
        items = self._repository.find_all(account_id=account_id)

        return [
            WatchlistItemResponse(
                id=item.id,
                symbol=item.symbol,
                name=item.name,
                market=item.market,
                created_at=item.created_at,
            )
            for item in items
        ]
