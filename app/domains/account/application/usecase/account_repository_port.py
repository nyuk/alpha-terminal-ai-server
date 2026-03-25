from abc import ABC, abstractmethod
from typing import Optional

from app.domains.account.domain.entity.account import Account


class AccountRepositoryPort(ABC):

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Account]:
        pass

    @abstractmethod
    def find_by_kakao_id(self, kakao_id: str) -> Optional[Account]:
        pass

    @abstractmethod
    def save(self, account: Account) -> Account:
        pass

    @abstractmethod
    def update(self, account: Account) -> Account:
        pass
