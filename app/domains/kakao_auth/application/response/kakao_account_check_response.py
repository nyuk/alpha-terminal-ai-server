from typing import Optional

from pydantic import BaseModel


class KakaoAccountCheckResponse(BaseModel):
    is_registered: bool
    account_id: Optional[int] = None
    email: str
    nickname: str
    temp_token_issued: bool = False
    temp_token_prefix: Optional[str] = None  # 앞 8자리만 노출 (확인용)

    # 내부 전달용 — 라우터에서 처리 후 응답 직렬화 시 제외
    temp_token: Optional[str] = None
    kakao_access_token: Optional[str] = None
    user_token: Optional[str] = None

    model_config = {"json_schema_extra": {"exclude": {"temp_token", "kakao_access_token", "user_token"}}}
