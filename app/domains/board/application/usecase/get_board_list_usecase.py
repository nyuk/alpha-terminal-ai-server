import math

from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.board.application.response.board_list_response import BoardListItemResponse, BoardListResponse
from app.domains.board.application.usecase.board_repository_port import BoardRepositoryPort


class GetBoardListUseCase:
    def __init__(self, board_repository: BoardRepositoryPort, account_repository: AccountRepositoryPort):
        self._board_repo = board_repository
        self._account_repo = account_repository

    def execute(self, page: int, size: int) -> BoardListResponse:
        boards = self._board_repo.find_paginated(page, size)
        total_count = self._board_repo.count_total()
        total_pages = math.ceil(total_count / size) if size > 0 else 0

        items = []
        for board in boards:
            account = self._account_repo.find_by_id(board.account_id)
            nickname = account.nickname if account else "알 수 없음"
            items.append(BoardListItemResponse(
                board_id=board.id,
                title=board.title,
                content=board.content,
                nickname=nickname,
                created_at=board.created_at,
                updated_at=board.updated_at,
            ))

        return BoardListResponse(
            items=items,
            page=page,
            total_pages=total_pages,
            total_count=total_count,
        )
