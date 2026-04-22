from typing import List, Optional

from sqlalchemy.orm import Session

from app.domains.notification.application.usecase.notification_repository_port import NotificationRepositoryPort
from app.domains.notification.domain.entity.notification import Notification
from app.domains.notification.infrastructure.mapper.notification_mapper import NotificationMapper
from app.domains.notification.infrastructure.orm.notification_orm import NotificationORM


class NotificationRepositoryImpl(NotificationRepositoryPort):
    def __init__(self, db: Session):
        self._db = db

    def save(self, notification: Notification) -> Notification:
        try:
            orm = NotificationMapper.to_orm(notification)
            self._db.add(orm)
            self._db.commit()
            self._db.refresh(orm)
            return NotificationMapper.to_entity(orm)
        except Exception:
            self._db.rollback()
            raise

    def find_all_by_user_id(self, user_id: int) -> List[Notification]:
        orms = (
            self._db.query(NotificationORM)
            .filter(NotificationORM.user_id == user_id)
            .order_by(NotificationORM.created_at.desc())
            .all()
        )
        return [NotificationMapper.to_entity(orm) for orm in orms]

    def find_by_id(self, notification_id: int) -> Optional[Notification]:
        orm = self._db.query(NotificationORM).filter(NotificationORM.id == notification_id).first()
        if orm is None:
            return None
        return NotificationMapper.to_entity(orm)

    def mark_read(self, notification_id: int) -> bool:
        try:
            orm = self._db.query(NotificationORM).filter(NotificationORM.id == notification_id).first()
            if orm is None:
                return False
            orm.is_read = True
            self._db.commit()
            return True
        except Exception:
            self._db.rollback()
            raise

    def mark_all_read(self, user_id: int) -> int:
        try:
            count = (
                self._db.query(NotificationORM)
                .filter(NotificationORM.user_id == user_id, NotificationORM.is_read == False)
                .update({"is_read": True})
            )
            self._db.commit()
            return count
        except Exception:
            self._db.rollback()
            raise

    def count_unread(self, user_id: int) -> int:
        return (
            self._db.query(NotificationORM)
            .filter(NotificationORM.user_id == user_id, NotificationORM.is_read == False)
            .count()
        )
