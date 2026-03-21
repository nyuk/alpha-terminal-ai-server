import logging
import uuid

from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.kakao_auth.application.response.kakao_account_check_response import KakaoAccountCheckResponse
from app.domains.kakao_auth.application.usecase.kakao_user_info_port import KakaoUserInfoPort
from app.domains.kakao_auth.application.usecase.request_kakao_access_token_port import RequestKakaoAccessTokenPort
from app.domains.kakao_auth.application.usecase.temp_token_store_port import TempTokenStorePort

logger = logging.getLogger(__name__)


class CheckKakaoUserRegistrationUseCase:

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
        if not code:
            raise ValueError("Authorization code is required")

        token = self._token_port.request(code)
        user = self._user_info_port.get_user_info(token.access_token)

        logger.debug(f"[Kakao] nickname={user.nickname}, email={user.email}")

        account = self._account_repository.find_by_email(user.email)

        if account:
            return KakaoAccountCheckResponse(
                is_registered=True,
                account_id=account.id,
                email=account.email,
                nickname=account.nickname,
                kakao_access_token=token.access_token,
            )

        temp_token = str(uuid.uuid4())
        self._temp_token_store.save(temp_token, token.access_token, user.kakao_id)

        return KakaoAccountCheckResponse(
            is_registered=False,
            email=user.email,
            nickname=user.nickname,
            temp_token_issued=True,
            temp_token_prefix=temp_token[:8],
            temp_token=temp_token,
        )
