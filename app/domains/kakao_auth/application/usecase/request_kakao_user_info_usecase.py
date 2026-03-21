from app.domains.kakao_auth.application.response.kakao_user_info_response import KakaoUserInfoResponse
from app.domains.kakao_auth.application.usecase.request_kakao_access_token_port import RequestKakaoAccessTokenPort
from app.domains.kakao_auth.application.usecase.kakao_user_info_port import KakaoUserInfoPort


class RequestKakaoUserInfoUseCase:

    def __init__(self, token_port: RequestKakaoAccessTokenPort, user_info_port: KakaoUserInfoPort):
        self._token_port = token_port
        self._user_info_port = user_info_port

    def execute(self, code: str) -> KakaoUserInfoResponse:
        if not code:
            raise ValueError("Authorization code is required")

        token = self._token_port.request(code)
        user = self._user_info_port.get_user_info(token.access_token)

        print(f"[Kakao] nickname={user.nickname}, email={user.email}")

        return KakaoUserInfoResponse(
            access_token=token.access_token,
            token_type=token.token_type,
            expires_in=token.expires_in,
            refresh_token=token.refresh_token,
            refresh_token_expires_in=token.refresh_token_expires_in,
            kakao_id=user.kakao_id,
            nickname=user.nickname,
            email=user.email,
        )
