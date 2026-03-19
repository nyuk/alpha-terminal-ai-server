from app.domains.account.domain.entity.account import Account
from app.domains.kakao_auth.application.usecase.check_kakao_account_registration_usecase import CheckKakaoAccountRegistrationUseCase
from tests.fakes.fake_account_repository import FakeAccountRepository
from tests.fakes.fake_kakao_token_adapter import FakeKakaoTokenAdapter
from tests.fakes.fake_temp_token_store import FakeTempTokenStore


def _make_usecase(account=None, email="user@kakao.com", nickname="홍길동", access_token="kakao_access_token_abc"):
    token_adapter = FakeKakaoTokenAdapter(access_token=access_token, email=email, nickname=nickname)
    repo = FakeAccountRepository(account=account)
    store = FakeTempTokenStore()
    usecase = CheckKakaoAccountRegistrationUseCase(
        token_port=token_adapter,
        user_info_port=token_adapter,
        account_repository=repo,
        temp_token_store=store,
    )
    return usecase, store


def test_기존_회원이면_is_registered_True():
    account = Account(id=1, email="user@kakao.com", kakao_id="12345678", nickname="홍길동")
    usecase, store = _make_usecase(account=account)

    result = usecase.execute("auth_code")

    assert result.is_registered is True
    assert result.account_id == 1
    assert result.temp_token_issued is False
    assert result.temp_token is None
    assert len(store.store) == 0


def test_미가입이면_is_registered_False():
    usecase, store = _make_usecase(account=None)

    result = usecase.execute("auth_code")

    assert result.is_registered is False
    assert result.account_id is None
    assert result.email == "user@kakao.com"
    assert result.nickname == "홍길동"


def test_미가입이면_임시_토큰이_발급된다():
    usecase, store = _make_usecase(account=None)

    result = usecase.execute("auth_code")

    assert result.temp_token_issued is True
    assert result.temp_token is not None
    assert len(result.temp_token) == 36  # UUID 형식


def test_임시_토큰_prefix는_앞_8자리():
    usecase, store = _make_usecase(account=None)

    result = usecase.execute("auth_code")

    assert result.temp_token_prefix == result.temp_token[:8]


def test_임시_토큰으로_kakao_access_token을_조회할_수_있다():
    access_token = "kakao_access_token_abc"
    usecase, store = _make_usecase(account=None, access_token=access_token)

    result = usecase.execute("auth_code")

    assert result.temp_token in store.store
    assert store.store[result.temp_token] == access_token
