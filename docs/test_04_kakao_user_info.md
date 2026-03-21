# Kakao 사용자 정보 조회

작성자: 이승욱
작성일: 2026-03-18
관련: TEST-04 (로컬 전용 — 커밋/푸시 금지)

---

## Backlog Title

시스템이 발급받은 액세스 토큰으로 Kakao 사용자 정보를 조회한다

---

## Success Criteria

- 별도의 추가 라우터 구성 없이 현재 구현된 Kakao 리다이렉션 콜백 API (GET /kakao-authentication/request-access-token-after-redirection) 에서 작업한다
- 시스템은 이전 단계에서 발급받은 Kakao 액세스 토큰을 사용하여 Kakao 사용자 정보 API를 호출한다
- Kakao API로부터 사용자 ID, 닉네임, 이메일 정보를 정상적으로 수신한다
- 수신 받은 닉네임과 이메일 정보를 콘솔창에 출력한다
- 액세스 토큰이 유효하지 않거나 만료된 경우 적절한 에러 응답을 반환한다
- 조회된 사용자 정보는 응답 데이터로 반환된다

---

## Todo

- [x] Kakao 액세스 토큰으로 사용자 정보를 조회하는 API를 구현한다
- [x] Kakao 사용자 정보 응답 구조를 정의한다
- [x] Kakao 사용자 정보 조회 실패 시 예외 처리를 구현한다

---

## 구현 구조

```
app/domains/kakao_auth/
├── adapter/inbound/api/kakao_auth_router.py
│   └── GET /kakao-authentication/request-access-token-after-redirection
└── adapter/outbound/external/kakao_user_info_adapter.py
```

## API 엔드포인트

```
GET /kakao-authentication/request-access-token-after-redirection?code=...&state=...
```

### Response 예시

```json
{
  "kakao_id": 4779956390,
  "email": "lubh@hanmail.net",
  "nickname": "su",
  "profile_image": ""
}
```

### 콘솔 출력 예시

```
[Kakao Login] nickname=su, email=lubh@hanmail.net
```

## 환경변수

| 키 | 설명 |
|----|------|
| `KAKAO_CLIENT_ID` | Kakao REST API 키 |
| `KAKAO_REDIRECT_URI` | 콜백 URI (http://localhost:33333/kakao-authentication/request-access-token-after-redirection) |

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-18 | 이승욱 | 최초 작성 및 구현 |
