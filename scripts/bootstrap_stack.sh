#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"
COMPOSE_FILE="${COMPOSE_FILE:-$ROOT_DIR/docker-compose.yml}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

compose() {
  docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

run_app_maintenance() {
  docker run --rm \
    --network quranapp-clean_default \
    -v "$ROOT_DIR/scripts:/scripts:ro" \
    -e APP_DB_HOST=clean-app-db \
    -e APP_DB_PORT=5432 \
    -e APP_DB_NAME="$APP_DB_NAME" \
    -e APP_DB_USER="$APP_DB_USER" \
    -e APP_DB_PASSWORD="$APP_DB_PASSWORD" \
    quranapp-clean-app-service:latest \
    python "$1"
}

set -a
source "$ENV_FILE"
set +a

echo "==> Building and starting local stack"
compose up -d --build clean-app-db clean-resource-db clean-resource-neo4j clean-resource-service clean-app-service

echo "==> Running app-service migrations"
compose exec -T clean-app-service alembic upgrade head

echo "==> Seeding app-owned prayer districts"
run_app_maintenance /scripts/database/prayer/seed_prayer_districts.py || echo "Warning: Prayer districts failed (likely API 429), continuing..."

if [[ -f "$ROOT_DIR/data/prayer-times.2026.json" ]]; then
  echo "==> Importing bulk prayer times file"
  docker run --rm \
    --network quranapp-clean_default \
    -v "$ROOT_DIR/scripts:/scripts:ro" \
    -v "$ROOT_DIR/data:/data:ro" \
    -e APP_DB_HOST=clean-app-db \
    -e APP_DB_PORT=5432 \
    -e APP_DB_NAME="$APP_DB_NAME" \
    -e APP_DB_USER="$APP_DB_USER" \
    -e APP_DB_PASSWORD="$APP_DB_PASSWORD" \
    quranapp-clean-app-service:latest \
    python /scripts/database/prayer/import_prayer_times.py
else
  echo "==> Skipping bulk prayer time import (data/prayer-times.2026.json not found)"
  echo "    Prayer times will sync on demand from the upstream public API and be cached locally."
fi

echo "==> Loading resource content"
compose exec -T clean-resource-service python scripts/database/content/load_knowledge_units.py
compose exec -T clean-resource-service python scripts/database/content/create_prescription_tables.py
compose exec -T clean-resource-service python scripts/database/content/load_prescription_content.py
compose exec -T clean-resource-service python scripts/database/graph/bootstrap_keyword_tables.py
compose exec -T clean-resource-service python scripts/database/graph/categorize_keywords.py
compose exec -T clean-resource-service python scripts/database/graph/embed_keywords.py
compose exec -T clean-resource-service python scripts/database/graph/migrate_to_neo4j.py
compose exec -T clean-resource-service python scripts/database/verify_setup.py

echo "==> Local stack is ready"
compose ps
