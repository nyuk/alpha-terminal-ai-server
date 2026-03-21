# 임시 토큰 기반 신규 계정 생성

작성자: 이승욱
백로그: TEST-09
로컬 전용 (커밋/푸시 금지)

---

## 목적

HTTP-Only Cookie의 임시 토큰(temp_token)으로 Redis를 조회하여
신규 계정을 생성하고, 생성된 account id(pk)와 Redis 유저 세션을 연결한다.

---

## 전제 조건

- TEST-08 (`GET /kakao-authentication/request-access-token-after-redirection`) 완료 후
  미가입 사용자의 경우 `temp_token` Cookie가 설정되어 있어야 함

---

## 엔드포인트

```
POST /account/register
```

### Request

- **Cookie**: `temp_token={uuid}`
- **Body** (JSON):
```json
{
  "nickname": "홍길동",
  "email": "hong@kakao.com"
}
```

### 성공 응답 (302 Redirect)

- Location: `{CORS_ALLOWED_FRONTEND_URL}` (기본값: `http://localhost:3000`)
- **Set-Cookie**:
  - `session_token={token}; HttpOnly; Max-Age=3600` (Redis 유저 세션)
  - `nickname=홍길동; Max-Age=3600`
  - `email=hong@kakao.com; Max-Age=3600`

### 에러 응답

| 상황 | HTTP Status | detail |
|------|-------------|--------|
| temp_token Cookie 없음 | 401 | "임시 토큰이 없습니다..." |
| 만료/존재하지 않는 temp_token | 400 | "임시 토큰이 만료되었거나 존재하지 않습니다" |
| DB 저장 실패 등 | 500 | "계정 생성 실패: ..." |

---

## 구현 흐름

```
POST /account/register
  Cookie: temp_token={uuid}
  Body: {nickname, email}
    ↓
RegisterAccountUseCase.execute(temp_token, nickname, email)   ← account 도메인
    ↓
① RedisTempTokenPortImpl.get(temp_token)
    → Redis: temp_token:{uuid} → {kakao_access_token, kakao_id}
    → 없으면 ValueError (만료/미존재)
② AccountRepositoryImpl.save(Account(email, kakao_id, nickname))
    → MySQL INSERT → Account(id=pk)
③ RedisTempTokenPortImpl.delete(temp_token)
    → Redis: temp_token:{uuid} 삭제
④ RedisAccountSessionAdapter.link_kakao_token(kakao_access_token, account.id)
    → Redis: kakao_access:{token} → account_id (TTL 6시간)
⑤ RedisAccountSessionAdapter.create(account.id)
    → Redis: session:{token} → {user_id: account_id, role: USER} (TTL 1시간)
    → session_token 반환
    ↓
RedirectResponse(frontend_url) + 3개 Cookie 설정
```

---

## 레이어별 역할

| 레이어 | 파일 | 역할 |
|--------|------|------|
| account Router | `account/adapter/inbound/api/account_router.py` | Cookie 추출, DI, Redirect 응답 |
| account UseCase | `account/application/usecase/register_account_usecase.py` | 핵심 비즈니스 로직 |
| account Port | `temp_token_port.py`, `account_session_port.py` | 추상화 |
| account Adapter | `redis_temp_token_port_impl.py` | Redis temp_token get/delete |
| account Adapter | `redis_account_session_adapter.py` | Redis 세션 생성, kakao 토큰 연결 |
| account Repository | `account_repository_impl.py` | MySQL 계정 저장 |

---

## Redis 키 구조

| 키 | 값 | TTL |
|----|-----|-----|
| `temp_token:{uuid}` | `{"kakao_access_token": "...", "kakao_id": "..."}` | 5분 (삭제 시 소멸) |
| `kakao_access:{token}` | `account_id` | 6시간 |
| `session:{token}` | `{"user_id": account_id, "role": "USER", "ttl_seconds": 3600}` | 1시간 |

---

## Success Criteria 검증

- [x] 이 작업은 account 도메인에서 진행한다 (RegisterAccountUseCase in account domain)
- [x] 클라이언트가 HTTP-Only Cookie의 temp_token + nickname, email로 회원가입 요청
- [x] Redis에서 임시 토큰을 조회하여 유효성 검증
- [x] 유효한 경우 신규 계정 생성
- [x] 만료/미존재 시 400 에러 반환
- [x] 계정 생성 후 임시 토큰 Redis에서 삭제
- [x] 임시 토큰의 Kakao Access Token을 Account id(pk)와 연결 (kakao_access:{token} → account_id)
- [x] 새 Redis 유저 토큰을 Account id(pk)와 연결 (session.user_id = account_id)
- [x] nickname, email + session_token을 Cookie에 설정
- [x] RedirectResponse로 CORS_ALLOWED_FRONTEND_URL로 응답
