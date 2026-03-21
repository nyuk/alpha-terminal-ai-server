# Kakao OAuth 인증 URL 요청

작성자: 이승욱
작성일: 2026-03-18
관련: TEST-03 (로컬 전용 — 커밋/푸시 금지)

---

## Backlog Title

인증되지 않은 사용자가 Kakao 인증 URL을 요청한다

---

## Success Criteria

- 인증되지 않은 사용자는 Kakao 인증 요청 시 인증 URL을 정상적으로 받을 수 있다
- 생성된 URL은 client_id, redirect_uri, response_type 등 필수 파라미터를 포함한다
- URL은 한 번 요청 시 즉시 반환되어 사용자가 Kakao 인증 페이지로 이동할 수 있다
- 잘못된 요청에 대해 적절한 예외 처리 및 메시지를 반환한다
- GET /kakao-authentication/request-oauth-link 구현
- 응답은 RedirectResponse를 통해 리다이렉션, 이후 작업도 Backend에서 이어받아 진행

---

## Todo

- [x] Kakao 인증 URL 생성 기능을 구현한다
- [x] Kakao 인증 URL 요청 API를 구현한다
- [x] Kakao 인증 URL 응답 구조를 정의한다

---

## 구현 구조

```
app/domains/kakao_auth/
├── domain/entity/kakao_oauth_params.py
├── application/
│   ├── usecase/generate_kakao_oauth_url_usecase.py
│   └── response/kakao_oauth_url_response.py
└── adapter/
    ├── inbound/api/kakao_auth_router.py
    └── outbound/in_memory/kakao_state_store.py
```

## API 엔드포인트

```
GET /kakao-authentication/request-oauth-link
→ RedirectResponse → https://kauth.kakao.com/oauth/authorize?...
```

## Kakao OAuth URL 형식

```
https://kauth.kakao.com/oauth/authorize
  ?response_type=code
  &client_id={KAKAO_CLIENT_ID}
  &redirect_uri={KAKAO_REDIRECT_URI}
  &state={random_state}
```

## 환경변수

| 키 | 설명 |
|----|------|
| `KAKAO_CLIENT_ID` | Kakao REST API 키 |
| `KAKAO_REDIRECT_URI` | 콜백 URI (예: http://localhost:33333/kakao-authentication/callback) |

---

## 변경 이력

| 날짜 | 작성자 | 내용 |
|------|--------|------|
| 2026-03-18 | 이승욱 | 최초 작성 및 구현 |
