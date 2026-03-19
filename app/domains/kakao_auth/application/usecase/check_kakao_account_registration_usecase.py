import uuid

from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.kakao_auth.application.response.kakao_account_check_response import KakaoAccountCheckResponse
from app.domains.kakao_auth.application.usecase.kakao_user_info_port import KakaoUserInfoPort
from app.domains.kakao_auth.application.usecase.request_kakao_access_token_port import RequestKakaoAccessTokenPort
from app.domains.kakao_auth.application.usecase.temp_token_store_port import TempTokenStorePort


class CheckKakaoAccountRegistrationUseCase:

    def __init__(
        self,
        token_port: RequestKakaoAccessTokenPort,
        user_info_port: KakaoUserInfoPort,
        account_repository: AccountRepositoryPort,
        temp_token_store: TempTokenStorePort,
    ):
        self._token_port = token_port
        self._user_info_port = user_info_port
        self._account_repository = account_repository
        self._temp_token_store = temp_token_store

    def execute(self, code: str) -> KakaoAccountCheckResponse:
        kakao_token = self._token_port.request(code)
        kakao_user = self._user_info_port.get_user_info(kakao_token.access_token)

        account = self._account_repository.find_by_email(kakao_user.email)

        if account is not None:
            return KakaoAccountCheckResponse(
                is_registered=True,
                account_id=account.id,
                email=account.email,
                nickname=account.nickname,
            )

        temp_token = str(uuid.uuid4())
        self._temp_token_store.save(temp_token, kakao_token.access_token)

        print(f"[TempToken] issued=True prefix={temp_token[:8]}...")

        return KakaoAccountCheckResponse(
            is_registered=False,
            email=kakao_user.email,
            nickname=kakao_user.nickname,
            temp_token_issued=True,
            temp_token_prefix=temp_token[:8],
            temp_token=temp_token,
        )
