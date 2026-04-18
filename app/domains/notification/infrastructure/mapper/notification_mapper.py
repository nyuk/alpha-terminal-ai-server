from datetime import datetime, timezone

from app.domains.notification.domain.entity.notification import Notification
from app.domains.notification.infrastructure.orm.notification_orm import NotificationORM


class NotificationMapper:
    @staticmethod
    def to_entity(orm: NotificationORM) -> Notification:
        created = orm.created_at
        if created is None:
            created = datetime.now(timezone.utc)
        return Notification(
            id=orm.id,
            user_id=orm.user_id,
            title=orm.title,
            body=orm.body,
            is_read=orm.is_read,
            created_at=created,
        )

    @staticmethod
    def to_orm(entity: Notification) -> NotificationORM:
        return NotificationORM(
            user_id=entity.user_id,
            title=entity.title,
            body=entity.body,
            is_read=entity.is_read,
        )
