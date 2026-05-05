from typing import Optional

from app.domains.kakao_auth.application.usecase.temp_token_store_port import TempTokenStorePort


class FakeTempTokenStore(TempTokenStorePort):

    def __init__(self):
        self.store: dict[str, str] = {}
        self.kakao_ids: dict[str, str] = {}

    def save(self, temp_token: str, kakao_access_token: str, kakao_id: str) -> None:
        self.store[temp_token] = kakao_access_token
        self.kakao_ids[temp_token] = kakao_id

    def get(self, temp_token: str) -> Optional[dict]:
        kakao_access_token = self.store.get(temp_token)
        if kakao_access_token is None:
            return None
        return {
            "kakao_access_token": kakao_access_token,
            "kakao_id": self.kakao_ids.get(temp_token, ""),
        }

    def delete(self, temp_token: str) -> None:
        self.store.pop(temp_token, None)
        self.kakao_ids.pop(temp_token, None)
