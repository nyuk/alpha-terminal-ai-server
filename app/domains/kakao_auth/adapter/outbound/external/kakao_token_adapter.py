import httpx
from app.domains.kakao_auth.application.usecase.kakao_token_port import KakaoTokenPort
from app.domains.kakao_auth.application.usecase.kakao_user_info_port import KakaoUserInfoPort
from app.domains.kakao_auth.application.usecase.request_kakao_access_token_port import RequestKakaoAccessTokenPort
from app.domains.kakao_auth.domain.entity.kakao_access_token import KakaoAccessToken
from app.domains.kakao_auth.domain.entity.kakao_user import KakaoUser

KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me"


class KakaoTokenAdapter(KakaoTokenPort, RequestKakaoAccessTokenPort, KakaoUserInfoPort):

    def __init__(self, client_id: str, redirect_uri: str):
        self._client_id = client_id
        self._redirect_uri = redirect_uri

    # RequestKakaoAccessTokenPort
    def request(self, code: str) -> KakaoAccessToken:
        response = httpx.post(
            KAKAO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": self._client_id,
                "redirect_uri": self._redirect_uri,
                "code": code,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        body = response.json()
        if response.status_code != 200 or "access_token" not in body:
            raise ValueError(f"Kakao token exchange failed: {body}")
        return KakaoAccessToken(
            access_token=body["access_token"],
            token_type=body.get("token_type", "bearer"),
            expires_in=body.get("expires_in", 0),
            refresh_token=body.get("refresh_token", ""),
            refresh_token_expires_in=body.get("refresh_token_expires_in", 0),
            scope=body.get("scope", ""),
        )

    # KakaoUserInfoPort
    def get_user_info(self, access_token: str) -> KakaoUser:
        return self._get_user_info(access_token)

    # KakaoTokenPort
    def exchange_code_for_user(self, code: str) -> KakaoUser:
        kakao_token = self.request(code)
        return self._get_user_info(kakao_token.access_token)

    def _get_user_info(self, access_token: str) -> KakaoUser:
        response = httpx.get(
            KAKAO_USER_INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = response.json()
        if response.status_code != 200:
            raise ValueError(f"Kakao user info failed: {data}")
        kakao_account = data.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        return KakaoUser(
            kakao_id=str(data["id"]),
            nickname=profile.get("nickname", ""),
            email=kakao_account.get("email", ""),
        )
