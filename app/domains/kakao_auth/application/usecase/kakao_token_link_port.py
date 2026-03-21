from abc import ABC, abstractmethod


class KakaoTokenLinkPort(ABC):

    @abstractmethod
    def save(self, account_id: int, kakao_access_token: str) -> None:
        """kakao_token:{account_id} = kakao_access_token 으로 Redis에 저장"""
        pass
