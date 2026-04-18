from typing import List

from app.domains.notification.application.usecase.notification_repository_port import NotificationRepositoryPort
from app.domains.notification.domain.entity.notification import Notification


class GetNotificationsUseCase:
    def __init__(self, repository: NotificationRepositoryPort):
        self._repository = repository

    def execute(self, user_id: int) -> List[Notification]:
        return self._repository.find_all_by_user_id(user_id)
