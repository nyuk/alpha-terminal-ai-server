from app.domains.board.domain.entity.board import Board
from app.domains.board.infrastructure.orm.board_orm import BoardORM


class BoardMapper:
    @staticmethod
    def to_entity(orm: BoardORM) -> Board:
        return Board(
            id=orm.id,
            title=orm.title,
            content=orm.content,
            account_id=orm.account_id,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    @staticmethod
    def to_orm(entity: Board) -> BoardORM:
        return BoardORM(
            title=entity.title,
            content=entity.content,
            account_id=entity.account_id,
        )
