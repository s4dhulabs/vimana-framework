#!/usr/bin/env bash
# Roomgate CI example: secure-path IDOR with dual auth.
set -euo pipefail

BASE_URL="${ROOMGATE_TARGET:-http://localhost:18104}"

vimana run roomgate \
  --target-url "$BASE_URL" \
  --room-path '/ws/secure/{id}' \
  --room-id-a room-a \
  --room-id-b room-b \
  --room-auth-a 'Bearer user-a' \
  --room-auth-b 'Bearer user-b' \
  --room-audit \
  --json --ci-mode --no-channels | tee /tmp/roomgate_secure.json

echo "High findings: $(jq '.summary.findings_high' /tmp/roomgate_secure.json)"
