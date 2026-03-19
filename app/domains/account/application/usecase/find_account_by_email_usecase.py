from typing import Optional

from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.account.domain.entity.account import Account


class FindAccountByEmailUseCase:

    def __init__(self, repository: AccountRepositoryPort):
        self._repository = repository

    def execute(self, email: str) -> Optional[Account]:
        if not email:
            return None
        return self._repository.find_by_email(email)
