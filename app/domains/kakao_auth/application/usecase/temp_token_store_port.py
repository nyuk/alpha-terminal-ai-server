from abc import ABC, abstractmethod


class TempTokenStorePort(ABC):

    @abstractmethod
    def save(self, temp_token: str, kakao_access_token: str) -> None:
        pass
