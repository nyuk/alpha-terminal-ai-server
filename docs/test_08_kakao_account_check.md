# Kakao 사용자 정보로 회원 가입 여부 확인

작성자: 이승욱
백로그: TEST-08
로컬 전용 (커밋/푸시 금지)

---

## 목적

Kakao 사용자 정보에서 추출한 이메일로 기존 회원 데이터베이스를 조회하여
가입 여부를 확인하고 결과를 반환한다.
주요 기능은 account 도메인에 구현한다.

---

## 엔드포인트

```
GET /kakao-authentication/request-access-token-after-redirection
```

### 성공 응답 - 기존 회원 (200 OK)

```json
{
  "is_registered": true,
  "account_id": 1,
  "email": "hong@kakao.com",
  "nickname": "홍길동"
}
```

### 성공 응답 - 미가입 (200 OK)

```json
{
  "is_registered": false,
  "account_id": null,
  "email": "hong@kakao.com",
  "nickname": "홍길동"
}
```

---

## 구현 흐름

```
GET /kakao-authentication/request-access-token-after-redirection?code=...
    ↓
CheckKakaoUserRegistrationUseCase.execute(code)   ← kakao_auth 레이어 (orchestrating)
    ↓
① KakaoTokenAdapter.request(code)                 → KakaoAccessToken
② KakaoTokenAdapter.get_user_info(access_token)   → KakaoUser (email 포함)
③ print(f"[Kakao] nickname=..., email=...")
④ AccountRepositoryImpl.find_by_email(email)      → Account? (account 도메인)
    ↓
    존재 → AccountCheckResponse(is_registered=True, account_id, email, nickname)
    없음 → AccountCheckResponse(is_registered=False, email, nickname)
```

---

## 레이어별 역할

| 레이어 | 파일 | 역할 |
|--------|------|------|
| kakao_auth UseCase | `check_kakao_user_registration_usecase.py` | orchestrating (토큰→사용자정보→회원조회) |
| account Port | `account_repository_port.py` | find_by_email 추상화 |
| account Adapter | `account_repository_impl.py` | MySQL DB 조회 |
| account Response | `account_check_response.py` | is_registered + 회원정보 DTO |
| Router | `kakao_authentication_router.py` | DB 세션 주입, usecase 실행 |

---

## Success Criteria 검증

- [x] 이 작업의 주요 기능은 account 도메인에 구현한다 (AccountRepositoryPort, AccountCheckResponse)
- [x] 별도의 추가 라우터 구성 없이 기존 GET /kakao-authentication/request-access-token-after-redirection 에서 작업한다
- [x] 이메일 정보를 사용해서 기존 회원 데이터베이스에서 일치하는 회원을 조회한다
- [x] 기존 회원이 존재하면 해당 회원 정보를 반환한다 (is_registered=True + account 정보)
- [x] 기존 회원이 존재하지 않으면 미가입 상태임을 식별할 수 있는 결과를 반환한다 (is_registered=False)
