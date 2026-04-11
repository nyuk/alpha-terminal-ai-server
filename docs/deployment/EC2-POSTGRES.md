# EC2에 PostgreSQL 올리기 (로컬 Docker와 동일)

로컬 개발용 모노레포 루트의 `docker-compose.yml` 에 정의된 `postgres` 서비스와 맞춥니다.

| 항목 | 로컬과 동일 |
|------|-------------|
| 이미지 | `pgvector/pgvector:pg16` |
| DB 이름 | 기본 `appdb` (`PG_DATABASE`) |
| 사용자 | 기본 `eddi` (`PG_USER`) |
| 비밀번호 | `.env` 의 `PG_PASSWORD` (로컬 예시와 같게 두거나, 운영은 강한 값으로 변경) |

API 컨테이너는 **`PG_HOST`에 Postgres 컨테이너 호스트명**을 써야 합니다. 이 저장소의 EC2 배포는 Docker 네트워크 **`alphadesk-network`** 를 쓰므로, 아래 Compose는 컨테이너 이름 **`alphadesk-postgres`** 로 띄우고, **`.env`에 다음을 넣습니다.**

```env
PG_HOST=alphadesk-postgres
PG_PORT=5432
PG_USER=eddi
PG_PASSWORD=<서버에서 안전한 비밀번호>
PG_DATABASE=appdb
```

`POSTGRES_*` 초기값과 `PG_*` 가 **반드시 같아야** 합니다. 위 Compose는 `--env-file .env` 로 `PG_*` 를 읽어 `POSTGRES_USER` 등에 넘깁니다.

---

## 1. 네트워크 (이미 있으면 생략)

GitHub Actions self-hosted 배포가 쓰는 네트워크와 같아야 API가 Postgres에 붙습니다.

```bash
docker network inspect alphadesk-network >/dev/null 2>&1 || docker network create alphadesk-network
```

---

## 2. Postgres 기동

레포를 EC2에 두는 경로가 `/home/ec2-user/alpha-terminal-ai-server` 라고 가정합니다.

**한 번에 (권장):** `.env` 에 `PG_USER` / `PG_PASSWORD` / `PG_DATABASE` 를 넣고, `PG_HOST=alphadesk-postgres` 까지 맞춘 뒤:

```bash
cd /home/ec2-user/alpha-terminal-ai-server
git pull   # 이 스크립트·compose 파일이 포함된 커밋 필요
./docs/deployment/ec2-up-postgres.sh
docker logs alphadesk-postgres --tail 30
```

**수동:**

```bash
cd /home/ec2-user/alpha-terminal-ai-server
docker compose -f docs/deployment/docker-compose.postgres.ec2.yml --env-file .env up -d
docker logs alphadesk-postgres --tail 30
```

데이터는 볼륨 **`alphadesk_pg_data`** 에 유지됩니다.

---

## 3. API 컨테이너가 새 `.env` 를 쓰게 하기

`.env` 를 수정했다면 API를 다시 띄워야 합니다.

- **GitHub Actions 배포를 쓰는 경우:** `main` 에 빈 커밋을 푸시하거나, EC2에서 Actions가 쓰는 것과 동일하게 `docker stop/rm alphadesk-api` 후 `docker run ... --env-file .env --network alphadesk-network ...` (팀의 배포 스크립트와 동일하게).
- 로컬에서 확인: `docker exec alphadesk-api env | grep PG_`

---

## 4. 동작 확인

```bash
# EC2 호스트에서 (Postgres 포트를 보안 그룹에 열지 않은 경우, 컨테이너 경유)
docker exec -it alphadesk-postgres psql -U "${PG_USER:-eddi}" -d "${PG_DATABASE:-appdb}" -c "SELECT 1"
```

API 기동 로그에 PostgreSQL 스키마 초기화 예외가 없어야 하고, 프론트에서 뉴스 **저장** 시 `POST /news/saved` 가 201 이어야 합니다.

---

## 5. 보안

- `PG_PASSWORD` 는 로컬 개발용 문자열을 그대로 쓰지 말고 EC2 전용으로 바꿉니다.
- Postgres **5432 포트를 보안 그룹에 퍼블릭으로 열 필요 없습니다.** API 컨테이너만 같은 Docker 네트워크로 접속하면 됩니다.
