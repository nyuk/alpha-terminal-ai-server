import json
from typing import Optional

import redis

from app.domains.kakao_auth.application.usecase.temp_token_store_port import TempTokenStorePort

TEMP_TOKEN_KEY_PREFIX = "temp_token:"
TEMP_TOKEN_TTL_SECONDS = 1800  # 30분


class RedisTempTokenAdapter(TempTokenStorePort):

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def save(self, temp_token: str, kakao_access_token: str, kakao_id: str) -> None:
        key = TEMP_TOKEN_KEY_PREFIX + temp_token
        self._redis.setex(key, TEMP_TOKEN_TTL_SECONDS, json.dumps({
            "kakao_access_token": kakao_access_token,
            "kakao_id": kakao_id,
        }))

    def get(self, temp_token: str) -> Optional[dict]:
        key = TEMP_TOKEN_KEY_PREFIX + temp_token
        data = self._redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    def delete(self, temp_token: str) -> None:
        self._redis.delete(TEMP_TOKEN_KEY_PREFIX + temp_token)
