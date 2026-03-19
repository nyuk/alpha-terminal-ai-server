import redis

from app.domains.kakao_auth.application.usecase.temp_token_store_port import TempTokenStorePort

TEMP_TOKEN_KEY_PREFIX = "temp_token:"
TEMP_TOKEN_TTL_SECONDS = 300  # 5분


class RedisTempTokenAdapter(TempTokenStorePort):

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def save(self, temp_token: str, kakao_access_token: str) -> None:
        key = TEMP_TOKEN_KEY_PREFIX + temp_token
        self._redis.setex(key, TEMP_TOKEN_TTL_SECONDS, kakao_access_token)
