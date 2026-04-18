from app.domains.notification.application.request.create_notification_request import CreateNotificationRequest
from app.domains.notification.application.usecase.notification_repository_port import NotificationRepositoryPort
from app.domains.notification.domain.entity.notification import Notification


class CreateNotificationUseCase:
    def __init__(self, repository: NotificationRepositoryPort):
        self._repository = repository

    def execute(self, request: CreateNotificationRequest) -> Notification:
        notification = Notification(
            user_id=request.user_id,
            title=request.title,
            body=request.body,
        )
        return self._repository.save(notification)
