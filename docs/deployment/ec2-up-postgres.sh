#!/usr/bin/env bash
# EC2에서 실행: alpha-terminal-ai-server 레포 루트의 .env 를 사용해 Postgres(로컬과 동일 이미지) 기동
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"
NETWORK=alphadesk-network
COMPOSE_FILE="$REPO_ROOT/docs/deployment/docker-compose.postgres.ec2.yml"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "missing .env at $ENV_FILE" >&2
  exit 1
fi
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "missing $COMPOSE_FILE (git pull 했는지 확인)" >&2
  exit 1
fi

docker network inspect "$NETWORK" >/dev/null 2>&1 || docker network create "$NETWORK"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
echo "OK: alphadesk-postgres on network $NETWORK"
echo "Ensure .env has PG_HOST=alphadesk-postgres then restart API (deploy or docker run again)."
