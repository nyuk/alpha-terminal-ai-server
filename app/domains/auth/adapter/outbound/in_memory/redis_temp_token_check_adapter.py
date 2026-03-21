import redis

from app.domains.auth.application.usecase.temp_token_check_port import TempTokenCheckPort

TEMP_TOKEN_KEY_PREFIX = "temp_token:"


class RedisTempTokenCheckAdapter(TempTokenCheckPort):

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def exists(self, temp_token: str) -> bool:
        key = TEMP_TOKEN_KEY_PREFIX + temp_token
        return self._redis.exists(key) > 0
