from app.domains.account.application.usecase.find_account_by_email_usecase import FindAccountByEmailUseCase
from app.domains.account.domain.entity.account import Account
from tests.fakes.fake_account_repository import FakeAccountRepository


def test_기존_회원이면_account_반환():
    account = Account(id=1, email="user@kakao.com", kakao_id="12345678", nickname="홍길동")
    repo = FakeAccountRepository(account=account)
    usecase = FindAccountByEmailUseCase(repo)

    result = usecase.execute("user@kakao.com")

    assert result is not None
    assert result.id == 1
    assert result.email == "user@kakao.com"


def test_미가입_회원이면_None_반환():
    repo = FakeAccountRepository(account=None)
    usecase = FindAccountByEmailUseCase(repo)

    result = usecase.execute("notexist@kakao.com")

    assert result is None


def test_이메일이_빈_문자열이면_None_반환():
    account = Account(id=1, email="user@kakao.com", kakao_id="12345678", nickname="홍길동")
    repo = FakeAccountRepository(account=account)
    usecase = FindAccountByEmailUseCase(repo)

    result = usecase.execute("")

    assert result is None
