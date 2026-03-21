# Kakao 액세스 토큰 교환 (리다이렉션 콜백)

작성자: 이승욱
백로그: TEST-05
로컬 전용 (커밋/푸시 금지)

---

## 목적

Kakao 인증 페이지에서 리다이렉션된 인가 코드(code)를 받아
Kakao OAuth 토큰 API에 액세스 토큰을 요청하고 반환한다.

---

## 엔드포인트

```
GET /kakao-authentication/request-access-token-after-redirection
```

### Query Parameters

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| code | string | 조건부 필수 | Kakao 인가 코드 |
| error | string | - | 인증 실패 시 에러 코드 |
| error_description | string | - | 에러 설명 |

### 성공 응답 (200 OK)

```json
{
  "access_token": "xxxxxx",
  "token_type": "bearer",
  "expires_in": 21599,
  "refresh_token": "yyyyyy",
  "refresh_token_expires_in": 5183999,
  "scope": "profile_nickname"
}
```

### 에러 응답

| 상황 | HTTP Status | detail |
|------|-------------|--------|
| code 누락 | 400 | "Authorization code is missing" |
| Kakao 에러 리다이렉션 | 400 | "Kakao OAuth error: {error} - {error_description}" |
| 유효하지 않은 code | 400 | "Kakao token exchange failed: {...}" |
| Kakao 서버 오류 | 502 | "Kakao token request failed: ..." |

---

## 구현 흐름

```
Kakao 인증 페이지
    ↓ (redirect with ?code=...)
GET /kakao-authentication/request-access-token-after-redirection
    ↓
RequestKakaoAccessTokenUseCase.execute(code)
    ↓
KakaoTokenAdapter.request(code)
    ↓ POST https://kauth.kakao.com/oauth/token
    ↓ grant_type=authorization_code, client_id, redirect_uri, code
    ↓
KakaoAccessTokenResponse 반환
```

---

## Kakao 토큰 API 요청 스펙

- **URL**: `https://kauth.kakao.com/oauth/token`
- **Method**: POST
- **Content-Type**: `application/x-www-form-urlencoded`

| 파라미터 | 값 |
|---------|-----|
| grant_type | authorization_code |
| client_id | Kakao REST API 키 |
| redirect_uri | 등록된 리다이렉트 URI |
| code | 인가 코드 |

---

## 관련 파일

| 역할 | 파일 |
|------|------|
| Router | `app/domains/kakao_auth/adapter/inbound/api/kakao_authentication_router.py` |
| UseCase | `app/domains/kakao_auth/application/usecase/request_kakao_access_token_usecase.py` |
| Port | `app/domains/kakao_auth/application/usecase/request_kakao_access_token_port.py` |
| Adapter | `app/domains/kakao_auth/adapter/outbound/external/kakao_token_adapter.py` |
| Response DTO | `app/domains/kakao_auth/application/response/kakao_access_token_response.py` |
| Entity | `app/domains/kakao_auth/domain/entity/kakao_access_token.py` |

---

## Success Criteria 검증

- [x] Kakao 인증 페이지에서 리다이렉션된 요청에 인가 코드(code)가 query parameter로 포함되어 있다
- [x] 액세스 토큰 발급 시 Kakao OAuth 기준(client_id, redirect_uri, code, grant_type)에 맞춰 요청이 처리된다
- [x] Kakao 토큰 API로부터 액세스 토큰을 정상적으로 수신한다
- [x] 인가 코드가 유효하지 않거나 누락된 경우 적절한 에러 응답을 반환한다 (400/502)
- [x] 발급된 액세스 토큰은 바로 API 요청에 사용 가능하며, 토큰 만료 시간 및 리프레시 토큰도 포함된다
