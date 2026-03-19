from abc import ABC, abstractmethod

from app.domains.kakao_auth.domain.entity.kakao_user import KakaoUser


class KakaoUserInfoPort(ABC):

    @abstractmethod
    def get_user_info(self, access_token: str) -> KakaoUser:
        pass
