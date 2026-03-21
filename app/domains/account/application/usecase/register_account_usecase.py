from app.domains.account.application.request.register_account_request import RegisterAccountRequest
from app.domains.account.application.response.register_account_response import RegisterAccountResponse
from app.domains.account.application.usecase.account_repository_port import AccountRepositoryPort
from app.domains.account.application.usecase.account_session_store_port import AccountSessionStorePort
from app.domains.account.application.usecase.kakao_token_store_port import KakaoTokenStorePort
from app.domains.account.application.usecase.temp_token_port import TempTokenPort
from app.domains.account.domain.entity.account import Account


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
        kakao_access_token = self._temp_token_port.find(temp_token)
        if not kakao_access_token:
            raise ValueError("임시 토큰이 유효하지 않거나 만료되었습니다.")

        account = self._account_repository.save(
            Account(email=request.email, kakao_id=request.email, nickname=request.nickname)
        )

        self._temp_token_port.delete(temp_token)

        self._kakao_token_store.save(account.id, kakao_access_token)

        session_token = self._session_store.create_session(account.id)

        print(f"[Register] account_id={account.id} email={account.email} session_prefix={session_token[:8]}...")

        return RegisterAccountResponse(
            account_id=account.id,
            nickname=account.nickname,
            email=account.email,
            session_token=session_token,
        )
