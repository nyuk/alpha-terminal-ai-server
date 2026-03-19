from typing import Optional

from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.account.domain.entity.account import Account


class FakeAccountRepository(AccountRepositoryPort):

    def __init__(self, account: Optional[Account] = None):
        self._account = account

    def find_by_email(self, email: str) -> Optional[Account]:
        if self._account and self._account.email == email:
            return self._account
        return None
