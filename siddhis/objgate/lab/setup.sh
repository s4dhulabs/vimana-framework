#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building objgate lab (Django REST Framework)..."
docker compose build
docker compose up -d

echo "Waiting for health..."
for _ in $(seq 1 40); do
  if curl -sf http://localhost:18105/health >/dev/null 2>&1; then
    echo "Lab ready at http://localhost:18105"
    echo "  OpenAPI:  http://localhost:18105/openapi.json"
    echo "  Catalog:  http://localhost:18105/orders/catalog"
    exit 0
  fi
  sleep 1
done

echo "Lab did not become healthy in time" >&2
docker compose logs --tail=30
exit 1
