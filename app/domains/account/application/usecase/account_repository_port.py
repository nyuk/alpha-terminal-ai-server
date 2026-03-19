from abc import ABC, abstractmethod
from typing import Optional

from app.domains.account.domain.entity.account import Account


class AccountRepositoryPort(ABC):

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Account]:
        pass
