from typing import Optional

from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.account.domain.entity.account import Account


class FakeAccountRepository(AccountRepositoryPort):

    def __init__(self, account: Optional[Account] = None):
        self._account = account
        self.saved_accounts: list[Account] = []

    def find_by_id(self, account_id: int) -> Optional[Account]:
        if self._account and self._account.id == account_id:
            return self._account
        return None

    def find_by_email(self, email: str) -> Optional[Account]:
        if self._account and self._account.email == email:
            return self._account
        return None

    def find_by_kakao_id(self, kakao_id: str) -> Optional[Account]:
        if self._account and self._account.kakao_id == kakao_id:
            return self._account
        return None

    def save(self, account: Account) -> Account:
        self._account = account
        self.saved_accounts.append(account)
        return account

    def update(self, account: Account) -> Account:
        self._account = account
        return account
