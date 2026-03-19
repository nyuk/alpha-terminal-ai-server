from dataclasses import dataclass


@dataclass
class KakaoUser:
    kakao_id: str
    nickname: str
    email: str = ""
