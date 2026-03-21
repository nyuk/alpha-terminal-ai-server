from abc import ABC, abstractmethod
from typing import Optional


class TempTokenPort(ABC):

    @abstractmethod
    def find(self, temp_token: str) -> Optional[str]:
        """temp_token으로 kakao_access_token 조회"""
        pass

    @abstractmethod
    def delete(self, temp_token: str) -> None:
        pass
