#!/usr/bin/env bash
# Objgate CI: open orders BOLA — expect high findings (exit 1).
set -euo pipefail
BASE_URL="${OBJGATE_TARGET:-http://localhost:18105}"

vimana run objgate \
  --target-url "$BASE_URL" \
  --obj-path '/api/orders/{id}/' \
  --obj-id-a 1 --obj-id-b 2 \
  --obj-audit --json --ci-mode --no-channels
