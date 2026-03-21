# 기존 회원 Kakao 로그인 후 Redis 사용자 토큰 발급

작성자: 이승욱
백로그: TEST-10
로컬 전용 (커밋/푸시 금지)

---

## 목적

기존 회원이 Kakao OAuth 인증을 완료하면
Redis 유저 세션 토큰을 발급하고 HTTP-Only Cookie로 전달한 뒤
Frontend로 Redirect한다.

---

## 엔드포인트

```
GET /kakao-authentication/request-access-token-after-redirection?code=...
```

### 기존 회원 응답 (302 Redirect)

- Location: `{CORS_ALLOWED_FRONTEND_URL}`
- **Set-Cookie**:
  - `user_token={uuid}; HttpOnly; Max-Age=3600`
  - `nickname=홍길동; Max-Age=3600`
  - `email=hong@kakao.com; Max-Age=3600`
  - `account_id=1; Max-Age=3600`

### 신규 회원 응답 (200 JSON — 기존 TEST-09 흐름 유지)

```json
{
  "is_registered": false,
  "email": "hong@kakao.com",
  "nickname": "홍길동",
  "temp_token_issued": true,
  "temp_token_prefix": "a1b2c3d4"
}
```
- `temp_token` Cookie (HttpOnly, 5분)

---

## 구현 흐름 (기존 회원)

```
GET /kakao-authentication/request-access-token-after-redirection?code=...
    ↓
CheckKakaoUserRegistrationUseCase.execute(code)
    ↓
① KakaoTokenAdapter.request(code)           → access_token
② KakaoTokenAdapter.get_user_info(token)    → email
③ AccountRepositoryImpl.find_by_email(email)→ Account (기존 회원)
    ↓ is_registered=True, kakao_access_token 포함
④ RedisAccountSessionAdapter.create(account_id)
    → Redis: session:{uuid} → {user_id: account_id, role: USER}   (1시간)
    → user_token 반환
⑤ RedisAccountSessionAdapter.save_account_kakao_token(account_id, kakao_access_token)
    → Redis: {account_id} → kakao_access_token                    (6시간)
    ↓
RedirectResponse(frontend_url)
+ user_token Cookie (HttpOnly)
+ nickname, email, account_id Cookie
```

---

## Redis 키 구조

| 키 | 값 | TTL |
|----|-----|-----|
| `session:{uuid}` | `{"user_id": account_id, "role": "USER", "ttl_seconds": 3600}` | 1시간 |
| `{account_id}` | `kakao_access_token` | 6시간 |

---

## 관련 파일

| 역할 | 파일 |
|------|------|
| Router | `kakao_auth/adapter/inbound/api/kakao_authentication_router.py` |
| UseCase | `kakao_auth/application/usecase/check_kakao_user_registration_usecase.py` |
| Response DTO | `kakao_auth/application/response/kakao_account_check_response.py` |
| Session Port | `account/application/usecase/account_session_port.py` |
| Session Adapter | `account/adapter/outbound/in_memory/redis_account_session_adapter.py` |

---

## Success Criteria 검증

- [x] 별도 라우터 없이 기존 GET /kakao-authentication/request-access-token-after-redirection 에서 처리
- [x] email로 회원 가입 여부 확인
- [x] UUID 기반 user_token 생성 후 Redis session:{uuid} → account_id 저장
- [x] Redis account_id → kakao_access_token 저장
- [x] user_token HTTP-Only Cookie 전달
- [x] 응답에 nickname, email, account_id 포함 (Cookie)
- [x] RedirectResponse로 CORS_ALLOWED_FRONTEND_URL 응답
