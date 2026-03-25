from abc import ABC, abstractmethod
from typing import Optional


class TempTokenPort(ABC):

    @abstractmethod
    def find(self, temp_token: str) -> Optional[dict]:
        """temp_token으로 kakao_access_token, kakao_id 조회"""
        pass

    @abstractmethod
    def delete(self, temp_token: str) -> None:
        pass
