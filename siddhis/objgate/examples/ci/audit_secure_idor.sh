#!/usr/bin/env bash
# Objgate CI: secure-path IDOR with dual auth.
set -euo pipefail
BASE_URL="${OBJGATE_TARGET:-http://localhost:18105}"

vimana run objgate \
  --target-url "$BASE_URL" \
  --obj-path '/api/secure/orders/{id}/' \
  --obj-id-a 1 --obj-id-b 2 \
  --obj-auth-a 'Bearer user-a-token' \
  --obj-auth-b 'Bearer user-b-token' \
  --obj-methods GET,PATCH \
  --obj-audit --json --ci-mode --no-channels | tee /tmp/objgate_secure.json

echo "High findings: $(jq '.summary.findings_high' /tmp/objgate_secure.json)"
