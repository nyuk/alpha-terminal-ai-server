from app.domains.kakao_auth.application.usecase.temp_token_store_port import TempTokenStorePort


class FakeTempTokenStore(TempTokenStorePort):

    def __init__(self):
        self.store: dict[str, str] = {}

    def save(self, temp_token: str, kakao_access_token: str) -> None:
        self.store[temp_token] = kakao_access_token
