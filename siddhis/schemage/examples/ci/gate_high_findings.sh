#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${SCHEMAGE_TARGET:-http://localhost:18107}"
vimana run schemage --target-url "$BASE_URL" \
  --gql-path /graphql --gql-audit --json --ci-mode --no-channels
