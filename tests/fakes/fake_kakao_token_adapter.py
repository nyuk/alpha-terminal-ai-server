from app.domains.kakao_auth.application.usecase.kakao_user_info_port import KakaoUserInfoPort
from app.domains.kakao_auth.application.usecase.request_kakao_access_token_port import RequestKakaoAccessTokenPort
from app.domains.kakao_auth.domain.entity.kakao_access_token import KakaoAccessToken
from app.domains.kakao_auth.domain.entity.kakao_user import KakaoUser


class FakeKakaoTokenAdapter(RequestKakaoAccessTokenPort, KakaoUserInfoPort):

    def __init__(self, access_token: str, email: str, nickname: str):
        self._access_token = access_token
        self._email = email
        self._nickname = nickname

    def request(self, code: str) -> KakaoAccessToken:
        return KakaoAccessToken(
            access_token=self._access_token,
            token_type="bearer",
            expires_in=21600,
            refresh_token="fake_refresh",
            refresh_token_expires_in=5184000,
            scope="profile_nickname account_email",
        )

    def get_user_info(self, access_token: str) -> KakaoUser:
        return KakaoUser(
            kakao_id="12345678",
            nickname=self._nickname,
            email=self._email,
        )
