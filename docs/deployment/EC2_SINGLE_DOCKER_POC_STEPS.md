# EC2 1대 + Docker (API + MySQL + Redis) PoC 배포 절차

`alpha-desk-ai-server` 기준. 도메인·HTTPS는 생략 가능(먼저 IP:포트로 검증 후 Nginx+Certbot 추가).

---

## 0. 사전 준비

- AWS 계정, 결제 수단
- 로컬 터미널에서 SSH 가능
- 저장소 접근(GitHub 등) 및 서버에 넣을 **`.env` 값** 목록(비밀은 레포에 커밋하지 말 것)

---

## 1. EC2 인스턴스 만들기

1. AWS 콘솔 → **EC2** → **인스턴스 시작**
2. **이름** 예: `alphadesk-poc`
3. **AMI:** Amazon Linux 2023
4. **인스턴스 유형:** `t3.micro`(또는 무료 티어 안내에 맞는 타입)
5. **키 페어:** 새로 생성 → `.pem` 다운로드(권한 `chmod 400`)
6. **네트워크 설정**
   - 퍼블릭 IP 자동 할당 허용
   - **보안 그룹 인바운드 규칙(초기 PoC):**
     - SSH **22** — 내 IP만(또는 임시로 0.0.0.0/0 후 반드시 좁히기)
     - HTTP **80** — `0.0.0.0/0`(나중에 Nginx용)
     - HTTPS **443** — `0.0.0.0/0`(TLS 적용 시)
     - 커스텀 TCP **33333** — `0.0.0.0/0`(직접 uvicorn 노출 테스트용; 운영에서는 80/443만 쓰는 것을 권장)
7. **스토리지:** 20~30 GiB gp3
8. **인스턴스 시작**

**탄력적 IP(고정 IP):** EC2 → 탄력적 IP 할당 → 인스턴스에 연결(재시작 시 IP 변하는 것 방지).

---

## 2. SSH 접속

```bash
ssh -i /path/to/key.pem ec2-user@<퍼블릭_IP>
```

(AMI가 Ubuntu면 사용자명은 `ubuntu`.)

---

## 3. Docker 설치 (Amazon Linux 2023)

```bash
sudo dnf update -y
sudo dnf install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
```

**로그아웃 후 다시 SSH** 접속해 `docker` 그룹 적용.

Docker Compose V2 확인:

```bash
docker compose version
```

**플러그인이 없을 때 (Amazon Linux 2023에서 `dnf`에 패키지가 없는 경우가 있음):**

```bash
sudo mkdir -p /usr/local/lib/docker/cli-plugins
# x86_64
sudo curl -SL "https://github.com/docker/compose/releases/download/v2.34.2/docker-compose-linux-x86_64" \
  -o /usr/local/lib/docker/cli-plugins/docker-compose
# Graviton(aarch64)이면 위 URL을 docker-compose-linux-aarch64 로 변경
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
docker compose version
```

(선택) `sudo dnf install -y docker-compose-plugin` 이 되는 환경이면 그것만으로도 충분합니다.

---

## 4. 코드 받기

```bash
sudo mkdir -p /opt/alphadesk && sudo chown ec2-user:ec2-user /opt/alphadesk
cd /opt/alphadesk
git clone <YOUR_REPO_URL> alpha-desk-ai-server
cd alpha-desk-ai-server
```

---

## 5. 서버용 Dockerfile 추가 (레포에 없을 때)

프로젝트 루트에 `Dockerfile` 예시:

```dockerfile
FROM python:3.12-slim-bookworm
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 33333
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "33333"]
```

> `kiwipiepy` 등이 빌드 실패하면 slim 대신 `python:3.12-bookworm` 이미지로 바꿔 재시도.

---

## 6. docker-compose.yml (API + MySQL + Redis + PostgreSQL)

프로젝트 루트에 `docker-compose.prod.yml` 등으로 저장. **PostgreSQL** 은 로컬 모노레포와 동일하게 `pgvector/pgvector:pg16` · DB `appdb` 등(자세한 절차는 [EC2-POSTGRES.md](./EC2-POSTGRES.md)):

```yaml
services:
  mysql:
    image: mysql:8.0
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-alphadesk}
      MYSQL_USER: ${MYSQL_USER:-alphadesk}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    command:
      - --character-set-server=utf8mb4
      - --collation-server=utf8mb4_unicode_ci
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h 127.0.0.1 -uroot -p\"$$MYSQL_ROOT_PASSWORD\" || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 30

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data

  postgres:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${PG_USER:-eddi}
      POSTGRES_PASSWORD: ${PG_PASSWORD}
      POSTGRES_DB: ${PG_DATABASE:-appdb}
    volumes:
      - pg_data:/var/lib/postgresql/data

  api:
    build: .
    restart: unless-stopped
    ports:
      - "33333:33333"
    env_file: .env
    environment:
      MYSQL_HOST: mysql
      MYSQL_PORT: "3306"
      MYSQL_DATABASE: ${MYSQL_DATABASE:-alphadesk}
      MYSQL_USER: ${MYSQL_USER:-alphadesk}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      REDIS_HOST: redis
      REDIS_PORT: "6379"
      PG_HOST: postgres
      PG_PORT: "5432"
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_started
      postgres:
        condition: service_started

volumes:
  mysql_data:
  redis_data:
  pg_data:
```

`.env`는 **서버에만** 두고, `MYSQL_*`·`REDIS_*`·**`PG_*`**(`PG_USER`, `PG_PASSWORD`, `PG_DATABASE`; 컨테이너 안 호스트명은 compose가 `PG_HOST=postgres`로 덮어씀)가 위와 맞아야 합니다. 나머지는 API 키, `CORS_ALLOWED_FRONTEND_URL` 등.

**최초 1회:** DB 스키마는 앱의 `Base.metadata.create_all` 또는 기존 마이그레이션 절차대로.

---

## 7. 서버에서 `.env` 작성

로컬 `.env`를 복사해 **비밀번호·URL만 서버 값으로 변경**:

- `MYSQL_*` — compose와 동일하게
- `REDIS_HOST` — 컨테이너 밖에서 테스트할 땐 무시되고, API 컨테이너 안에서는 compose의 `REDIS_HOST=redis`가 적용
- `PG_USER`, `PG_PASSWORD`, `PG_DATABASE` — `postgres` 서비스의 `POSTGRES_*` 와 동일해야 함(GitHub Actions만 쓰고 compose 없이 띄우는 경우는 [EC2-POSTGRES.md](./EC2-POSTGRES.md))
- `CORS_ALLOWED_FRONTEND_URL` — 실제 프론트 주소(예: `https://app.example.com` 또는 PoC 중 `http://<EC2_IP>:3000` 등)
- `FRONTEND_AUTH_CALLBACK_URL`, Kakao Redirect URI와 일치

```bash
cd /opt/alphadesk/alpha-desk-ai-server
nano .env   # 또는 vi
chmod 600 .env
```

---

## 8. 기동

```bash
cd /opt/alphadesk/alpha-desk-ai-server
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f api
```

브라우저/ curl:

```bash
curl -s http://<퍼블릭_IP>:33333/
```

---

## 9. 점검·운영 팁

| 항목 | 내용 |
|------|------|
| 로그 | `docker compose logs -f api` |
| 재시작 | `docker compose restart api` |
| 갱신 배포 | `git pull && docker compose up -d --build` |
| 방화벽 | 보안 그룹에서 **22는 반드시 본인 IP로 제한** |
| HTTPS | 나중에 **Nginx + Let’s Encrypt** 또는 **ALB + ACM** 추가 |

---

## 10. (선택) 80 포트로만 열고 싶을 때

EC2에 Nginx 설치 후 `proxy_pass http://127.0.0.1:33333;`, Certbot으로 443까지 구성. 보안 그룹에서 **33333을 닫고** 80/443만 개방.

---

이 순서대로면 **월 비용은 이전에 말한 EC2+EBS 수준(대략 USD 12~25/월 전후)** 에 가깝게 PoC를 돌릴 수 있습니다. RDS·ElastiCache·ALB는 쓰지 않습니다.
