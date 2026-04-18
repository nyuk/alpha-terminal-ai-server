from app.domains.notification.application.usecase.notification_repository_port import NotificationRepositoryPort


class GetUnreadCountUseCase:
    def __init__(self, repository: NotificationRepositoryPort):
        self._repository = repository

    def execute(self, user_id: int) -> int:
        return self._repository.count_unread(user_id)
