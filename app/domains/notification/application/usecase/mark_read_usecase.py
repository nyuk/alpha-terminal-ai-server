from app.domains.notification.application.usecase.notification_repository_port import NotificationRepositoryPort


class MarkReadUseCase:
    def __init__(self, repository: NotificationRepositoryPort):
        self._repository = repository

    def execute(self, notification_id: int) -> bool:
        return self._repository.mark_read(notification_id)


class MarkAllReadUseCase:
    def __init__(self, repository: NotificationRepositoryPort):
        self._repository = repository

    def execute(self, user_id: int) -> int:
        return self._repository.mark_all_read(user_id)
