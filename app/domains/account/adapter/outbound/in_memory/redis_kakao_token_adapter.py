import redis

from app.domains.account.application.usecase.kakao_token_store_port import KakaoTokenStorePort

KAKAO_TOKEN_KEY_PREFIX = "kakao_token:"
KAKAO_TOKEN_TTL_SECONDS = 3600 * 24 * 7  # 7일


class RedisKakaoTokenAdapter(KakaoTokenStorePort):

    def __init__(self, redis_client: redis.Redis):
        self._redis = redis_client

    def save(self, account_id: int, kakao_access_token: str) -> None:
        key = KAKAO_TOKEN_KEY_PREFIX + str(account_id)
        self._redis.setex(key, KAKAO_TOKEN_TTL_SECONDS, kakao_access_token)
