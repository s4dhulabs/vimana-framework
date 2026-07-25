#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${FETCHBANE_TARGET:-http://localhost:18106}"
vimana run fetchbane --target-url "$BASE_URL" \
  --ssrf-endpoint /preview --ssrf-audit --json --ci-mode --no-channels
