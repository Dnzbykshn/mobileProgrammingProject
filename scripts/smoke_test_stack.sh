#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

set -a
source "$ENV_FILE"
set +a

APP_URL="http://127.0.0.1:${APP_SERVICE_HOST_PORT:-18000}"
RESOURCE_URL="http://127.0.0.1:${RESOURCE_SERVICE_HOST_PORT:-18100}"

echo "==> Health"
curl -fsS "$APP_URL/health"
echo
curl -fsS "$RESOURCE_URL/health"
echo

echo "==> App facade /content/sources"
curl -fsS "$APP_URL/api/v1/content/sources"
echo

echo "==> App facade /content/search"
curl -fsS -H 'Content-Type: application/json' \
  -d '{"query":"sabır","limit":2,"source_types":["quran"]}' \
  "$APP_URL/api/v1/content/search"
echo

echo "==> App locations"
curl -fsS "$APP_URL/api/v1/locations/countries"
echo

echo "==> App prayer times (on-demand sync)"
curl -fsS "$APP_URL/api/v1/prayer-times/today?district_id=9146"
echo

echo "==> Resource graph context"
curl -fsS -H "X-Service-Token: $RESOURCE_SERVICE_TOKEN" -H 'Content-Type: application/json' \
  -d '{"text":"gelecek kaygısı yaşıyorum","keywords":["kaygı","gelecek"],"top_k":5}' \
  "$RESOURCE_URL/api/v1/resources/contexts/graph"
echo

echo "==> Smoke test passed"
