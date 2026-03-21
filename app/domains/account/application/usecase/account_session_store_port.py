from abc import ABC, abstractmethod


class AccountSessionStorePort(ABC):

    @abstractmethod
    def create_session(self, account_id: int) -> str:
        """account_id 기반 세션 생성 후 session token 반환"""
        pass
