# BL-BE-18

**Backlog Type**
Maintenance / Infrastructure

**Backlog Title**
모바일 환경 OAuth 리다이렉트 URL 환경변수화 — KAKAO_REDIRECT_URI, CORS, 콜백 URL

---

## 1. 배경

- 백엔드 `.env`의 `KAKAO_REDIRECT_URI`가 `http://localhost:33333/...`으로 고정되어 있었다.
- 모바일(외부 기기)에서 `http://<서버IP>:3000`으로 접근하면, 카카오 인증 후 브라우저가
  `localhost:33333`에 직접 접속을 시도해 연결 실패가 발생했다.
- 인증 완료 후 `FRONTEND_AUTH_CALLBACK_URL`이 `http://localhost:3000/auth-callback`으로
  고정되어 있어 모바일에서 리다이렉트가 실패하고 로그인 화면으로 되돌아가는 문제가 있었다.
- `CORS_ALLOWED_FRONTEND_URL`도 `localhost:3000`으로 고정되어 있어 모바일 접근 시 CORS 오류 가능성이 있었다.

## 2. 해결 방향

세 환경변수를 `.env`에서 명시적으로 설정 가능하도록 하고,
모바일 테스트 환경에서는 서버 IP(`192.168.1.1`)를 기준으로 설정한다.
프론트엔드의 Next.js rewrites 프록시(BL-FE-37)와 함께 동작하도록 경로를 맞춘다.

## 3. 변경 내용

| 환경변수 | 기존 | 변경 |
|---|---|---|
| `KAKAO_REDIRECT_URI` | `http://localhost:33333/kakao-authentication/request-access-token-after-redirection` | `http://192.168.1.1:3000/api/kakao-authentication/request-access-token-after-redirection` |
| `CORS_ALLOWED_FRONTEND_URL` | (기본값 `http://localhost:3000`) | `http://192.168.1.1:3000` |
| `FRONTEND_AUTH_CALLBACK_URL` | (기본값 `http://localhost:3000/auth-callback`) | `http://192.168.1.1:3000/auth-callback` |

## 4. 관련 백로그

- **BL-FE-37** — Next.js rewrites 프록시 (`/api/*` → `localhost:33333`)
  카카오 리다이렉트가 `192.168.1.1:3000/api/...`로 오면 Next.js가 백엔드로 프록시한다.

## 5. 카카오 개발자 콘솔

다음 Redirect URI를 **추가** 등록해야 한다 (기존 URI 유지):
```
http://192.168.1.1:3000/api/kakao-authentication/request-access-token-after-redirection
```

## 6. Success Criteria

| ID | 기준 |
|----|------|
| SC-1 | 모바일에서 카카오 로그인 후 대시보드로 정상 진입한다. |
| SC-2 | 기존 로컬 PC 환경(localhost)에서도 로그인이 정상 동작한다. |
| SC-3 | `.env.example`에 세 환경변수가 주석과 함께 명시된다. |

## 7. 완료 정의

- [x] `.env` — 세 환경변수 설정
- [x] `.env.example` — 예시값 및 주석 추가
- [x] 모바일 카카오 로그인 테스트 통과
