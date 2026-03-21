from pydantic import BaseModel


class RegisterAccountResponse(BaseModel):
    account_id: int
    nickname: str
    email: str

    # 내부 전달용 — 라우터에서 쿠키 세팅 후 응답 직렬화 시 제외
    session_token: str
