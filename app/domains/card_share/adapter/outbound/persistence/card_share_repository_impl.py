from typing import Optional

from sqlalchemy import func, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domains.card_share.domain.entity.card_comment import CardComment
from app.domains.card_share.domain.entity.card_like import CardLike
from app.domains.card_share.domain.entity.shared_card import SharedCard
from app.domains.card_share.infrastructure.mapper.card_share_mapper import (
    orm_to_card_comment,
    orm_to_card_like,
    orm_to_shared_card,
    shared_card_to_orm,
)
from app.domains.card_share.infrastructure.orm.card_comment_orm import CardCommentORM
from app.domains.card_share.infrastructure.orm.card_like_orm import CardLikeORM
from app.domains.card_share.infrastructure.orm.shared_card_orm import SharedCardORM


class CardShareRepositoryImpl:
    def __init__(self, db: Session):
        self._db = db

    # ── Shared Cards ──────────────────────────────────────────────────────────

    def save(self, card: SharedCard) -> SharedCard:
        try:
            orm = shared_card_to_orm(card)
            self._db.add(orm)
            self._db.commit()
            self._db.refresh(orm)
            return orm_to_shared_card(orm)
        except Exception:
            self._db.rollback()
            raise

    def find_by_id(self, card_id: int) -> Optional[SharedCard]:
        orm = self._db.query(SharedCardORM).filter(SharedCardORM.id == card_id).first()
        return orm_to_shared_card(orm) if orm else None

    def find_all(self, limit: int = 20, offset: int = 0) -> tuple[list[SharedCard], int]:
        total = self._db.query(SharedCardORM).count()
        orms = (
            self._db.query(SharedCardORM)
            .order_by(SharedCardORM.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [orm_to_shared_card(o) for o in orms], total

    def delete(self, card_id: int) -> bool:
        try:
            orm = self._db.query(SharedCardORM).filter(SharedCardORM.id == card_id).first()
            if not orm:
                return False
            self._db.delete(orm)
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            raise

    # ── Likes ─────────────────────────────────────────────────────────────────

    def find_like(self, card_id: int, liker_ip: str, account_id: Optional[int] = None) -> Optional[CardLike]:
        """로그인 사용자는 account_id, 익명은 IP로 기존 좋아요 탐색."""
        query = self._db.query(CardLikeORM).filter(CardLikeORM.shared_card_id == card_id)
        if account_id:
            orm = query.filter(CardLikeORM.liker_account_id == account_id).first()
        else:
            orm = query.filter(
                CardLikeORM.liker_account_id.is_(None),
                CardLikeORM.liker_ip == liker_ip,
            ).first()
        return orm_to_card_like(orm) if orm else None

    def add_like(self, card_id: int, liker_ip: str, account_id: Optional[int]) -> bool:
        """좋아요 추가. 이미 존재하면 False 반환."""
        try:
            like_orm = CardLikeORM(
                shared_card_id=card_id,
                liker_ip=liker_ip,
                liker_account_id=account_id,
            )
            self._db.add(like_orm)
            self._db.query(SharedCardORM).filter(SharedCardORM.id == card_id).update(
                {"like_count": SharedCardORM.like_count + 1}
            )
            self._db.commit()
            return True
        except IntegrityError:
            self._db.rollback()
            return False

    def remove_like(self, card_id: int, liker_ip: str, account_id: Optional[int] = None) -> bool:
        """좋아요 취소. 없으면 False 반환."""
        query = self._db.query(CardLikeORM).filter(CardLikeORM.shared_card_id == card_id)
        if account_id:
            orm = query.filter(CardLikeORM.liker_account_id == account_id).first()
        else:
            orm = query.filter(
                CardLikeORM.liker_account_id.is_(None),
                CardLikeORM.liker_ip == liker_ip,
            ).first()
        if not orm:
            return False
        try:
            self._db.delete(orm)
            self._db.query(SharedCardORM).filter(SharedCardORM.id == card_id).update(
                {"like_count": func.greatest(SharedCardORM.like_count - 1, 0)}
            )
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            raise

    def get_like_count(self, card_id: int) -> int:
        orm = self._db.query(SharedCardORM).filter(SharedCardORM.id == card_id).first()
        return orm.like_count if orm else 0

    def find_liked_card_ids(
        self, card_ids: list[int], liker_ip: str, account_id: Optional[int] = None
    ) -> set[int]:
        """현재 사용자가 좋아요한 카드 ID set 반환."""
        if not card_ids:
            return set()
        query = self._db.query(CardLikeORM.shared_card_id).filter(
            CardLikeORM.shared_card_id.in_(card_ids)
        )
        if account_id:
            query = query.filter(CardLikeORM.liker_account_id == account_id)
        else:
            query = query.filter(
                CardLikeORM.liker_account_id.is_(None),
                CardLikeORM.liker_ip == liker_ip,
            )
        return {row[0] for row in query.all()}

    # ── Comments ──────────────────────────────────────────────────────────────

    def add_comment(self, comment: CardComment) -> CardComment:
        try:
            orm = CardCommentORM(
                shared_card_id=comment.shared_card_id,
                content=comment.content,
                author_nickname=comment.author_nickname,
                author_account_id=comment.author_account_id,
                author_ip=comment.author_ip,
            )
            self._db.add(orm)
            self._db.query(SharedCardORM).filter(SharedCardORM.id == comment.shared_card_id).update(
                {"comment_count": SharedCardORM.comment_count + 1}
            )
            self._db.commit()
            self._db.refresh(orm)
            return orm_to_card_comment(orm)
        except Exception:
            self._db.rollback()
            raise

    def find_comments(self, card_id: int) -> list[CardComment]:
        orms = (
            self._db.query(CardCommentORM)
            .filter(CardCommentORM.shared_card_id == card_id)
            .order_by(CardCommentORM.created_at.asc())
            .all()
        )
        return [orm_to_card_comment(o) for o in orms]
