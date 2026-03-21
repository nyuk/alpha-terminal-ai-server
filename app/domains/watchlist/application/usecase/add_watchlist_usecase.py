from app.domains.watchlist.application.request.add_watchlist_request import AddWatchlistRequest
from app.domains.watchlist.application.response.watchlist_response import WatchlistItemResponse
from app.domains.watchlist.application.usecase.watchlist_repository_port import WatchlistRepositoryPort
from app.domains.watchlist.domain.entity.watchlist_item import WatchlistItem


class AddWatchlistUseCase:
    def __init__(self, repository: WatchlistRepositoryPort):
        self._repository = repository

    def execute(self, request: AddWatchlistRequest) -> WatchlistItemResponse:
        existing = self._repository.find_by_symbol(request.symbol)
        if existing:
            raise ValueError("이미 등록된 종목입니다.")

        item = WatchlistItem(
            symbol=request.symbol,
            name=request.name,
            market=request.market,
        )

        saved = self._repository.save(item)

        return WatchlistItemResponse(
            id=saved.id,
            symbol=saved.symbol,
            name=saved.name,
            market=saved.market,
            created_at=saved.created_at,
        )
