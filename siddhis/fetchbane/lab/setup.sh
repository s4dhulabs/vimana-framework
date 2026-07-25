#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"
echo "Building fetchbane lab..."
docker compose build
docker compose up -d
echo "Waiting for health..."
for _ in $(seq 1 30); do
  if curl -sf http://localhost:18106/health >/dev/null 2>&1; then
    echo "Lab ready at http://localhost:18106 (canary inside: 127.0.0.1:9999/secret)"
    exit 0
  fi
  sleep 1
done
echo "Lab did not become healthy" >&2
docker compose logs --tail=20
exit 1
