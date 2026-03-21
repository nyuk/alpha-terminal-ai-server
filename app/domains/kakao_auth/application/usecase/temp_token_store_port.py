from abc import ABC, abstractmethod
from typing import Optional


class TempTokenStorePort(ABC):

    @abstractmethod
    def save(self, temp_token: str, kakao_access_token: str, kakao_id: str) -> None:
        pass

    @abstractmethod
    def get(self, temp_token: str) -> Optional[dict]:
        pass

    @abstractmethod
    def delete(self, temp_token: str) -> None:
        pass
