from abc import ABC, abstractmethod
from typing import List, Optional

from app.domains.notification.domain.entity.notification import Notification


class NotificationRepositoryPort(ABC):
    @abstractmethod
    def save(self, notification: Notification) -> Notification:
        pass

    @abstractmethod
    def find_all_by_user_id(self, user_id: int) -> List[Notification]:
        pass

    @abstractmethod
    def find_by_id(self, notification_id: int) -> Optional[Notification]:
        pass

    @abstractmethod
    def mark_read(self, notification_id: int) -> bool:
        pass

    @abstractmethod
    def mark_all_read(self, user_id: int) -> int:
        pass

    @abstractmethod
    def count_unread(self, user_id: int) -> int:
        pass
