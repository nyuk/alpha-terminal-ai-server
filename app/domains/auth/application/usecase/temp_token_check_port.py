from abc import ABC, abstractmethod


class TempTokenCheckPort(ABC):

    @abstractmethod
    def exists(self, temp_token: str) -> bool:
        pass
