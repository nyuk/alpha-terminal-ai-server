import uuid

import redis

from app.domains.account.application.usecase.account_session_store_port import AccountSessionStorePort
from app.domains.auth.domain.entity.session import Session
from app.domains.auth.domain.value_object.user_role import UserRole
from app.domains.auth.adapter.outbound.in_memory.redis_session_adapter import RedisSessionAdapter

SESSION_TTL_SECONDS = 3600 * 24 * 7  # 7일


class RedisAccountSessionAdapter(AccountSessionStorePort):

    def __init__(self, redis_client: redis.Redis):
        self._session_adapter = RedisSessionAdapter(redis_client)

    def create_session(self, account_id: int) -> str:
        token = str(uuid.uuid4())
        session = Session(token=token, user_id=str(account_id), role=UserRole.USER, ttl_seconds=SESSION_TTL_SECONDS)
        self._session_adapter.save(session)
        return token
