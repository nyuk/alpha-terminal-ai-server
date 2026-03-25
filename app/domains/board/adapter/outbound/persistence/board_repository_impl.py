from typing import List

from sqlalchemy.orm import Session

from app.domains.board.application.usecase.board_repository_port import BoardRepositoryPort
from app.domains.board.domain.entity.board import Board
from app.domains.board.infrastructure.mapper.board_mapper import BoardMapper
from app.domains.board.infrastructure.orm.board_orm import BoardORM


class BoardRepositoryImpl(BoardRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def save(self, board: Board) -> Board:
        orm = BoardMapper.to_orm(board)
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return BoardMapper.to_entity(orm)

    def find_paginated(self, page: int, size: int) -> List[Board]:
        offset = (page - 1) * size
        orms = (
            self._db.query(BoardORM)
            .order_by(BoardORM.created_at.desc())
            .offset(offset)
            .limit(size)
            .all()
        )
        return [BoardMapper.to_entity(orm) for orm in orms]

    def count_total(self) -> int:
        return self._db.query(BoardORM).count()
