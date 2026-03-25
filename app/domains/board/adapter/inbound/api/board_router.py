from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domains.account.adapter.outbound.persistence.account_repository_impl import AccountRepositoryImpl
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter
from app.domains.board.adapter.outbound.persistence.board_repository_impl import BoardRepositoryImpl
from app.domains.board.application.response.board_list_response import BoardListResponse, BoardListItemResponse
from app.domains.board.application.usecase.get_board_list_usecase import GetBoardListUseCase
from app.domains.board.domain.entity.board import Board
from app.infrastructure.cache.redis_client import redis_client
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/board", tags=["board"])

_session_adapter = RedisSessionAdapter(redis_client)


class CreateBoardRequest(BaseModel):
    title: str
    content: str


@router.post("", response_model=BoardListItemResponse, status_code=201)
async def create_board(
    request: CreateBoardRequest,
    account_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    parsed_account_id = int(account_id)
    account_repository = AccountRepositoryImpl(db)
    account = account_repository.find_by_id(parsed_account_id)
    if not account:
        raise HTTPException(status_code=401, detail="존재하지 않는 계정입니다.")

    board_repository = BoardRepositoryImpl(db)
    saved = board_repository.save(Board(
        title=request.title,
        content=request.content,
        account_id=parsed_account_id,
    ))

    return BoardListItemResponse(
        board_id=saved.id,
        title=saved.title,
        content=saved.content,
        nickname=account.nickname,
        created_at=saved.created_at,
        updated_at=saved.updated_at,
    )


@router.get("/list", response_model=BoardListResponse)
async def get_board_list(
    page: int = 1,
    size: int = 10,
    account_id: Optional[str] = Cookie(default=None),
    db: Session = Depends(get_db),
):
    if not account_id:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")

    board_repository = BoardRepositoryImpl(db)
    account_repository = AccountRepositoryImpl(db)
    usecase = GetBoardListUseCase(board_repository, account_repository)
    return usecase.execute(page=page, size=size)
