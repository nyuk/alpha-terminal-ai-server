# Kakao 사용자 정보 조회 (액세스 토큰 활용)

작성자: 이승욱
백로그: TEST-07
로컬 전용 (커밋/푸시 금지)

---

## 목적

이전 단계(TEST-05)에서 발급된 액세스 토큰을 즉시 활용하여
Kakao 사용자 정보 API를 호출하고, kakao_id / nickname / email을 반환한다.
별도 라우터 추가 없이 기존 엔드포인트 내에서 처리한다.

---

## 엔드포인트

```
GET /kakao-authentication/request-access-token-after-redirection
```

### 성공 응답 (200 OK)

```json
{
  "access_token": "xxxxxx",
  "token_type": "bearer",
  "expires_in": 21599,
  "refresh_token": "yyyyyy",
  "refresh_token_expires_in": 5183999,
  "kakao_id": "1234567890",
  "nickname": "홍길동",
  "email": "hong@kakao.com"
}
```

### 콘솔 출력 (서버 로그)

```
[Kakao] nickname=홍길동, email=hong@kakao.com
```

### 에러 응답

| 상황 | HTTP Status | detail |
|------|-------------|--------|
| code 누락 | 400 | "Authorization code is missing" |
| 유효하지 않은 code | 400 | "Kakao token exchange failed: {...}" |
| 만료된 액세스 토큰 | 502 | "Kakao request failed: ..." |
| Kakao 서버 오류 | 502 | "Kakao request failed: ..." |

---

## 구현 흐름

```
GET /kakao-authentication/request-access-token-after-redirection?code=...
    ↓
RequestKakaoUserInfoUseCase.execute(code)
    ↓
① KakaoTokenAdapter.request(code)          → KakaoAccessToken
    ↓ POST https://kauth.kakao.com/oauth/token
② KakaoTokenAdapter.get_user_info(token)   → KakaoUser
    ↓ GET https://kapi.kakao.com/v2/user/me
③ print(f"[Kakao] nickname=..., email=...")
    ↓
KakaoUserInfoResponse 반환
```

---

## 관련 파일

| 역할 | 파일 |
|------|------|
| Router | `app/domains/kakao_auth/adapter/inbound/api/kakao_authentication_router.py` |
| UseCase | `app/domains/kakao_auth/application/usecase/request_kakao_user_info_usecase.py` |
| Response DTO | `app/domains/kakao_auth/application/response/kakao_user_info_response.py` |
| Token Port | `app/domains/kakao_auth/application/usecase/request_kakao_access_token_port.py` |
| UserInfo Port | `app/domains/kakao_auth/application/usecase/kakao_user_info_port.py` |
| Adapter | `app/domains/kakao_auth/adapter/outbound/external/kakao_token_adapter.py` |
| Entity | `app/domains/kakao_auth/domain/entity/kakao_user.py` |

---

## Success Criteria 검증

- [x] 별도의 추가 라우터 구성 없이 기존 GET /kakao-authentication/request-access-token-after-redirection 에서 작업한다
- [x] 이전 단계에서 발급받은 액세스 토큰으로 Kakao 사용자 정보 API를 호출한다
- [x] Kakao API로부터 사용자 ID, 닉네임, 이메일 정보를 정상적으로 수신한다
- [x] 수신 받은 닉네임과 이메일 정보를 콘솔창에 출력한다 (print)
- [x] 액세스 토큰이 유효하지 않거나 만료된 경우 502 에러 응답을 반환한다
- [x] 조회된 사용자 정보는 응답 데이터로 반환된다
