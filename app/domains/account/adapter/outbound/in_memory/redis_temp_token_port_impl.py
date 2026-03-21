from typing import Optional

import redis

from app.domains.account.application.usecase.temp_token_port import TempTokenPort

TEMP_TOKEN_KEY_PREFIX = "temp_token:"


class RedisTempTokenPortImpl(TempTokenPort):

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def find(self, temp_token: str) -> Optional[str]:
        key = TEMP_TOKEN_KEY_PREFIX + temp_token
        value = self._redis.get(key)
        return value if value else None

    def delete(self, temp_token: str) -> None:
        key = TEMP_TOKEN_KEY_PREFIX + temp_token
        self._redis.delete(key)
