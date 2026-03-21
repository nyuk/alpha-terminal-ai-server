from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.domains.watchlist.adapter.outbound.persistence.watchlist_repository_impl import WatchlistRepositoryImpl
from app.domains.watchlist.application.request.add_watchlist_request import AddWatchlistRequest
from app.domains.watchlist.application.response.watchlist_response import WatchlistItemResponse
from app.domains.watchlist.application.usecase.add_watchlist_usecase import AddWatchlistUseCase
from app.domains.watchlist.application.usecase.get_watchlist_usecase import GetWatchlistUseCase
from app.domains.watchlist.application.usecase.remove_watchlist_usecase import RemoveWatchlistUseCase
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.post("", response_model=WatchlistItemResponse, status_code=201)
async def add_watchlist(request: AddWatchlistRequest, db: Session = Depends(get_db)):
    repository = WatchlistRepositoryImpl(db)
    usecase = AddWatchlistUseCase(repository)
    try:
        return usecase.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("", response_model=List[WatchlistItemResponse])
async def get_watchlist(db: Session = Depends(get_db)):
    repository = WatchlistRepositoryImpl(db)
    usecase = GetWatchlistUseCase(repository)
    return usecase.execute()


@router.delete("/{item_id}", status_code=204)
async def remove_watchlist(item_id: int, db: Session = Depends(get_db)):
    repository = WatchlistRepositoryImpl(db)
    usecase = RemoveWatchlistUseCase(repository)
    try:
        usecase.execute(item_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
