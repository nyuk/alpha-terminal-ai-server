import logging

from app.domains.account.application.request.register_account_request import RegisterAccountRequest
from app.domains.account.application.response.register_account_response import RegisterAccountResponse
from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.account.application.usecase.account_session_store_port import AccountSessionStorePort
from app.domains.account.application.usecase.kakao_token_store_port import KakaoTokenStorePort
from app.domains.account.application.usecase.temp_token_port import TempTokenPort
from app.domains.account.domain.entity.account import Account

logger = logging.getLogger(__name__)


class AccountLinkConflictError(Exception):
    pass


class RegisterAccountUseCase:

    def __init__(
        self,
        account_repository: AccountRepositoryPort,
        temp_token_port: TempTokenPort,
        kakao_token_store: KakaoTokenStorePort,
        session_store: AccountSessionStorePort,
    ):
        self._account_repository = account_repository
        self._temp_token_port = temp_token_port
        self._kakao_token_store = kakao_token_store
        self._session_store = session_store

    def execute(self, temp_token: str, request: RegisterAccountRequest) -> RegisterAccountResponse:
        temp_token_data = self._temp_token_port.find(temp_token)
        if not temp_token_data:
            raise ValueError("임시 토큰이 유효하지 않거나 만료되었습니다.")

        kakao_access_token = temp_token_data.get("kakao_access_token")
        kakao_id = temp_token_data.get("kakao_id")
        if not kakao_access_token or not kakao_id:
            raise ValueError("임시 토큰 정보가 올바르지 않습니다.")

        account = self._account_repository.find_by_kakao_id(kakao_id)
        if account is None:
            existing_email_account = self._account_repository.find_by_email(request.email)
            if existing_email_account:
                # 과거 버그로 kakao_id 대신 email이 저장된 계정은 현재 Kakao ID로 복구한다.
                if existing_email_account.kakao_id == existing_email_account.email:
                    existing_email_account.kakao_id = kakao_id
                    existing_email_account.nickname = request.nickname
                    account = self._account_repository.update(existing_email_account)
                else:
                    raise AccountLinkConflictError("이미 다른 카카오 계정에 연결된 이메일입니다.")
            else:
                account = self._account_repository.save(
                    Account(email=request.email, kakao_id=kakao_id, nickname=request.nickname)
                )

        self._temp_token_port.delete(temp_token)

        self._kakao_token_store.save(account.id, kakao_access_token)

        session_token = self._session_store.create_session(account.id)

        logger.debug(f"[Register] account_id={account.id} email={account.email} session_prefix={session_token[:8]}...")

        return RegisterAccountResponse(
            account_id=account.id,
            nickname=account.nickname,
            email=account.email,
            session_token=session_token,
        )
