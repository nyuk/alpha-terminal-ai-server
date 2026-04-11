# CI/CD — GitHub Actions 자동 배포 가이드

## 개요

`main` 브랜치에 push 또는 PR merge가 발생하면 GitHub Actions가 자동으로 Docker 이미지를 빌드하고 AWS EC2에 배포한다.

**수동 docker 명령어 불필요. main merge만 하면 배포 완료.**

---

## 배포 흐름

```
main push / PR merge
  │
  ├─ [GitHub 서버 - ubuntu-latest]
  │    build-and-push
  │      1. docker buildx build (linux/arm64)
  │      2. ghcr.io/writism/alpha-terminal-api:latest push
  │
  └─ [EC2 self-hosted runner]
       deploy
         1. docker pull ghcr.io/writism/alpha-terminal-api:latest
         2. docker stop/rm alphadesk-api
         3. docker run --env-file /home/ec2-user/alpha-terminal-ai-server/.env
         4. health check (http://localhost:33333/docs)
```

---

## 워크플로우 파일

| 레포 | 파일 | 이미지 | Runner 레이블 |
|---|---|---|---|
| alpha-terminal-ai-server | `.github/workflows/main.yml` | `ghcr.io/writism/alpha-terminal-api:latest` | `alpha-terminal-api` |
| alpha-terminal-frontend | `.github/workflows/main.yml` | `ghcr.io/writism/multi-agent-ui:latest` | `multi-agent-ui` |

---

## EC2 Self-hosted Runner

### 위치
```
/home/ec2-user/alpha-terminal-ai-server/actions-runner/   ← BE runner
/home/ec2-user/alpha-terminal-frontend/actions-runner/    ← FE runner (추정)
```

### 서비스 상태 확인
```bash
sudo systemctl status actions.runner.*
```

### 재시작 (필요 시)
```bash
sudo systemctl restart actions.runner.writism-alpha-terminal-ai-server.alpha-terminal-api
```

---

## GitHub Secrets 설정 (레포 Settings > Secrets)

| Secret | 용도 |
|---|---|
| `REPO_USER` | ghcr.io 사용자명 (writism) |
| `GHCR_TOKEN` | ghcr.io push 권한 PAT (`write:packages`) |
| `FRONTEND_ENV` | FE `.env` 파일 전체 내용 |

---

## 플랫폼 구조 (중요)

| 환경 | 아키텍처 |
|---|---|
| GitHub Actions 서버 (`ubuntu-latest`) | x86_64 (amd64) |
| AWS EC2 (t4g, Graviton) | arm64 |
| 로컬 맥 (M1/M2) | arm64 |

GitHub Actions는 x86_64 서버에서 QEMU 에뮬레이션으로 arm64 이미지를 빌드한다.
`docker/build-push-action`의 `platforms: linux/arm64`가 cross-compile을 담당하므로
**Dockerfile의 `FROM`에 `--platform=linux/arm64`를 하드코딩하면 안 된다.**

### 왜 문제가 되나

```dockerfile
# ❌ 잘못된 방법 — QEMU SIGILL 크래시 유발
FROM --platform=linux/arm64 node:20-alpine

# ✅ 올바른 방법 — build-push-action이 플랫폼 처리
FROM node:20-alpine
```

`FROM --platform` 고정 시 GitHub Actions의 x86 서버가 QEMU로 arm64를 에뮬레이션하는데,
Next.js static page 생성 단계처럼 연산이 많은 구간에서 SIGILL(Illegal Instruction)로 크래시 난다.

```
qemu: uncaught target signal 4 (Illegal instruction) - core dumped
⨯ Next.js build worker exited with code: null and signal: SIGILL
```

---

## 배포 후 502 Bad Gateway 발생 시

### 원인

`docker stop/rm/run`으로 컨테이너를 교체하면 Docker 네트워크 내 **IP 주소가 바뀐다.**
nginx는 이전 컨테이너의 IP를 캐싱하고 있어서 새 컨테이너에 연결하지 못하고 502를 반환한다.

```
구 alphadesk-web → 172.18.0.3  (nginx가 기억하는 IP)
신 alphadesk-web → 172.18.0.5  (실제 새 컨테이너 IP)
→ nginx가 172.18.0.3으로 요청 → 연결 실패 → 502
```

### 해결 방법

배포 후 502가 발생하면 EC2에서 nginx를 재시작한다:

```bash
docker restart alphadesk-nginx
```

### 근본적 해결 (향후 개선)

nginx 설정에서 `resolver` 지시어를 추가하면 Docker DNS를 통해 컨테이너 이름을 동적으로 재조회해 자동으로 해결된다.

---

## 수동 배포 시 환경변수 잘림 주의

### 원인

EC2에서 `docker run -e KEY=VALUE ...` 방식으로 긴 환경변수를 직접 입력하거나,
`cat > file.env << 'EOF'` heredoc으로 복사할 때 **긴 URL이 터미널에서 잘려서** 저장될 수 있다.

```bash
# ❌ 터미널에서 잘린 예시
KAKAO_REDIRECT_URI=https://alpha-desk.duckdns.org/api/kakao-authentication/request-access-token-aft
# → KOE006 에러 발생 (Kakao Redirect URI 불일치)
```

### 확인 방법

```bash
# 실행 중인 컨테이너 환경변수 확인
docker exec alphadesk-api env | grep KAKAO_REDIRECT_URI | cat

# EC2 .env 파일 확인 ($ = 정상 줄 끝)
grep KAKAO_REDIRECT_URI /home/ec2-user/alpha-terminal-ai-server/.env | cat -A
```

### 해결 방법

EC2의 `.env` 파일을 env-file로 사용해서 재시작:

```bash
docker stop alphadesk-api && docker rm alphadesk-api && \
docker run -d \
  --name alphadesk-api \
  -p 33333:33333 \
  --env-file /home/ec2-user/alpha-terminal-ai-server/.env \
  --network alphadesk-network \
  --ulimit nofile=32768:65536 \
  --restart unless-stopped \
  ghcr.io/writism/alpha-terminal-api:latest
```

### 근본적 해결

**수동 배포 하지 않기.** GitHub Actions가 항상 EC2의 `.env` 파일을 기반으로 배포하므로
main merge만 하면 환경변수 잘림 문제가 발생하지 않는다.

---

## 주의사항

- BE 컨테이너는 EC2의 `/home/ec2-user/alpha-terminal-ai-server/.env` 파일을 env-file로 사용
- `.env`에 새 환경변수 추가 시 EC2에서 직접 파일 수정 필요 (Actions로 자동화 안 됨)
- `main` 이외 브랜치 push는 Actions 미실행
- Runner가 중단된 경우 deploy job이 대기 상태로 멈춤 → EC2에서 서비스 재시작 필요
- Dockerfile `FROM`에 `--platform` 하드코딩 금지 (QEMU SIGILL 크래시)
- 배포 후 502 발생 시 `docker restart alphadesk-nginx` 실행

---

## 뉴스 저장(`POST /news/saved`)과 PostgreSQL

메타데이터는 **MySQL**, 기사 본문 JSON은 **PostgreSQL(JSONB)** 에 둡니다. EC2 `.env`의 **`PG_HOST`는 API 컨테이너 기준**이어야 합니다. 같은 Docker 네트워크에 Postgres 서비스 이름이 `postgres`이면 `PG_HOST=postgres`처럼 지정하고, **`PG_HOST=localhost`는 컨테이너 안에서는 호스트 DB를 가리키지 않습니다.**

Postgres가 없거나 연결이 실패해도 API는 기동하고, 저장 시 MySQL만 성공하도록 동작할 수 있습니다(본문·일부 분석 기능은 제한). 운영에서 본문 저장까지 쓰려면 Postgres를 띄우고 `PG_USER`, `PG_PASSWORD`, `PG_DATABASE` 등을 맞춥니다.

**EC2에 Postgres 올리기(로컬 Docker와 동일 이미지·볼륨 패턴):** [EC2-POSTGRES.md](./EC2-POSTGRES.md) · `docs/deployment/docker-compose.postgres.ec2.yml`
