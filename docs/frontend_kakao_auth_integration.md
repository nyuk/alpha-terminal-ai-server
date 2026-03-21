# Frontend Kakao 인증 연동 가이드

작성자: 이승욱
대상: FE 담당자 (김민정)

---

## 전체 흐름 요약

```
[신규 회원]
카카오 로그인 버튼
  → GET /kakao-authentication/request-oauth-link
  → Kakao 인증 페이지
  → GET /kakao-authentication/request-access-token-after-redirection
  → is_registered: false → 회원가입 페이지 이동 (temp_token Cookie 자동 세팅)
  → 회원가입 폼 입력 (nickname, email)
  → POST /account/register
  → 메인 페이지 이동 (session_token Cookie 자동 세팅)

[기존 회원]
카카오 로그인 버튼
  → GET /kakao-authentication/request-oauth-link
  → Kakao 인증 페이지
  → GET /kakao-authentication/request-access-token-after-redirection
  → is_registered: true → 메인 페이지로 자동 Redirect (user_token Cookie 자동 세팅)
```

---

## Step 1. 카카오 로그인 버튼

로그인 버튼 클릭 시 백엔드 URL로 이동시킨다.
(fetch/axios가 아닌 브라우저 페이지 이동)

```tsx
// 예시
const handleKakaoLogin = () => {
  window.location.href = 'http://localhost:33333/kakao-authentication/request-oauth-link'
}

<button onClick={handleKakaoLogin}>카카오로 로그인</button>
```

> **주의**: `fetch()` 또는 `axios`로 호출하면 안 됩니다.
> 반드시 `window.location.href` 로 브라우저가 직접 이동해야
> Kakao 인증 페이지 redirect와 Cookie 세팅이 정상 동작합니다.

---

## Step 2. 리다이렉션 콜백 처리

Kakao 인증 완료 후 백엔드가 자동으로 아래 두 경우로 분기한다.

### 2-A. 기존 회원 (is_registered: true)

백엔드가 직접 `http://localhost:3000` 으로 302 Redirect한다.

- 프론트가 별도로 처리할 것 없음
- 브라우저 Cookie에 자동 세팅됨:

| Cookie | 설명 |
|--------|------|
| `user_token` | Redis 세션 토큰 (HttpOnly) |
| `session_token` | 세션 토큰 (HttpOnly) |
| `nickname` | 사용자 닉네임 |
| `email` | 사용자 이메일 |
| `account_id` | DB PK |

→ **메인 페이지**에서 Cookie를 읽어 로그인 상태를 표시하면 됨

---

### 2-B. 신규 회원 (is_registered: false)

백엔드가 아래 JSON을 응답한다:

```json
{
  "is_registered": false,
  "account_id": null,
  "email": "user@kakao.com",
  "nickname": "홍길동",
  "temp_token_issued": true,
  "temp_token_prefix": "08e54b3e",
  "temp_token": "08e54b3e-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

브라우저 Cookie에 `temp_token` (HttpOnly) 이 자동 세팅된다.

**프론트가 해야 할 일:**

1. 이 JSON 응답이 Kakao redirect URL에서 발생하므로, 해당 URL을 프론트 라우터에서 처리해야 한다.

   ```
   http://localhost:3000/kakao-callback  (또는 별도 처리 페이지)
   ```

   > 단, 현재 Kakao redirect URI는 백엔드(`localhost:33333`)로 설정되어 있어
   > 프론트가 직접 콜백을 받지 않는다. 백엔드가 처리 후 프론트로 redirect한다.

2. 백엔드로부터 신규 회원 JSON을 받으면, **회원가입 페이지로 이동**시킨다.

   ```tsx
   // 예: 백엔드 redirect 후 프론트 /signup 페이지에서 처리
   // URL에 email, nickname을 query string으로 포함시켜 전달하거나
   // 별도 상태 관리로 처리
   ```

---

## Step 3. 회원가입 페이지 구현

**페이지 경로 예시**: `/signup`

### 화면 구성

- nickname 입력 필드 (Kakao 닉네임 기본값으로 pre-fill 권장)
- email 입력 필드 (Kakao 이메일 기본값으로 pre-fill 권장)
- "가입하기" 버튼

### API 호출

```tsx
const handleRegister = async () => {
  const response = await fetch('http://localhost:33333/account/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',   // ← 반드시 필요 (Cookie 자동 포함)
    body: JSON.stringify({ nickname, email }),
  })
  // 302 redirect → 브라우저가 자동으로 localhost:3000으로 이동
  // response.redirected === true 이면 메인 페이지로 이동 처리
}
```

> **`credentials: 'include'` 필수**
> 이 옵션이 없으면 `temp_token` Cookie가 요청에 포함되지 않아 400 에러 발생

### 요청 스펙

```
POST http://localhost:33333/account/register
Content-Type: application/json
Cookie: temp_token={uuid}   ← credentials: include로 자동 포함

Body:
{
  "nickname": "홍길동",
  "email": "user@kakao.com"
}
```

### 성공 응답

- 302 Redirect → `http://localhost:3000`
- Cookie 자동 세팅:

| Cookie | 설명 |
|--------|------|
| `session_token` | Redis 세션 토큰 (HttpOnly) |
| `nickname` | 사용자 닉네임 |
| `email` | 사용자 이메일 |

### 에러 처리

| 상황 | HTTP | 처리 방법 |
|------|------|-----------|
| temp_token 없음 | 401 | 로그인 페이지로 이동 |
| temp_token 만료 (5분 초과) | 400 | "다시 카카오 로그인 해주세요" 안내 |
| 서버 오류 | 500 | 에러 메시지 표시 |

---

## Step 4. 메인 페이지 로그인 상태 처리

회원가입/로그인 완료 후 `localhost:3000`으로 redirect되면
Cookie에서 사용자 정보를 읽어 표시한다.

```tsx
// HttpOnly가 아닌 Cookie는 JS에서 읽기 가능
const getCookie = (name: string) => {
  const match = document.cookie.match(new RegExp(`(^| )${name}=([^;]+)`))
  return match ? decodeURIComponent(match[2]) : null
}

const nickname = getCookie('nickname')   // "홍길동"
const email = getCookie('email')         // "user@kakao.com"
const accountId = getCookie('account_id') // "1"

// HttpOnly Cookie (session_token, user_token)는 JS에서 읽을 수 없음
// → API 요청 시 자동으로 포함됨 (credentials: 'include')
```

---

## 환경변수 정리

| 변수 | 값 |
|------|-----|
| 백엔드 Base URL | `http://localhost:33333` |
| Kakao 로그인 URL | `http://localhost:33333/kakao-authentication/request-oauth-link` |
| 회원가입 API | `POST http://localhost:33333/account/register` |
| 프론트 Base URL | `http://localhost:3000` |

---

## 주의사항 요약

1. Kakao 로그인은 반드시 `window.location.href` 사용 (fetch 금지)
2. `/account/register` 호출 시 반드시 `credentials: 'include'` 포함
3. temp_token은 **5분** 안에 회원가입 완료해야 함
4. session_token, user_token은 HttpOnly라 JS에서 직접 읽기 불가 → API 호출 시 자동 포함
