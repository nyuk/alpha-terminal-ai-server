from typing import List, Optional

from sqlalchemy.orm import Session

from app.domains.board.application.usecase.board_repository_port import BoardRepositoryPort
from app.domains.board.domain.entity.board import Board
from app.domains.board.infrastructure.mapper.board_mapper import BoardMapper
from app.domains.board.infrastructure.orm.board_orm import BoardORM


class BoardRepositoryImpl(BoardRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def save(self, board: Board) -> Board:
        try:
            orm = BoardMapper.to_orm(board)
            self._db.add(orm)
            self._db.commit()
            self._db.refresh(orm)
            return BoardMapper.to_entity(orm)
        except Exception:
            self._db.rollback()
            raise

    def find_by_id(self, board_id: int) -> Optional[Board]:
        orm = self._db.query(BoardORM).filter(BoardORM.id == board_id).first()
        return BoardMapper.to_entity(orm) if orm else None

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

    def update(self, board_id: int, title: str, content: str) -> Optional[Board]:
        try:
            orm = self._db.query(BoardORM).filter(BoardORM.id == board_id).first()
            if orm is None:
                return None
            orm.title = title
            orm.content = content
            self._db.commit()
            self._db.refresh(orm)
            return BoardMapper.to_entity(orm)
        except Exception:
            self._db.rollback()
            raise

    def delete(self, board_id: int) -> bool:
        try:
            orm = self._db.query(BoardORM).filter(BoardORM.id == board_id).first()
            if orm is None:
                return False
            self._db.delete(orm)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            raise
